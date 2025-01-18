import csv
import numpy as np
from scipy.stats import poisson
import datetime
import get_fixtures
from footer import get_footer

# Holds league-wide stats
class LeagueData:
    def __init__(self):
        self.totalHomeGoals = 0
        self.totalAwayGoals = 0
        self.avgHomeGoalsPerMatch = 0
        self.avgAwayGoalsPerMatch = 0
        self.totalMatches = 0

# Holds stats for a single team
class TeamData:
    def __init__(self):
        self.avgHomeGoalsScored = 0
        self.avgHomeGoalsAllowed = 0
        self.totalHomeGoalsScored = 0
        self.totalHomeGoalsAllowed = 0
        self.avgAwayGoalsScored = 0
        self.avgAwayGoalsAllowed = 0
        self.totalAwayGoalsScored = 0
        self.totalAwayGoalsAllowed = 0
        self.totalMatches = 0
        self.homeMatches = 0
        self.awayMatches = 0

# Load match data and update stats
def loadData(leagueData, teamStats):
    totalLeagueHomeGoals = 0
    totalLeagueAwayGoals = 0
    totalMatches = 0
    
    with open('/home/jimmyrustles/mysite/data/final_dataset.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row[5] == 'FTHG' or not row[5]: 
                continue
            
            homeGoals = int(row[5])
            awayGoals = int(row[6])
            homeTeam = row[3]
            awayTeam = row[4]
            
            totalLeagueHomeGoals += homeGoals
            totalLeagueAwayGoals += awayGoals

            if homeTeam not in teamStats:
                teamStats[homeTeam] = TeamData()
            if awayTeam not in teamStats:
                teamStats[awayTeam] = TeamData()

            # Update team data
            teamStats[homeTeam].totalHomeGoalsScored += homeGoals
            teamStats[homeTeam].totalHomeGoalsAllowed += awayGoals
            teamStats[awayTeam].totalAwayGoalsScored += awayGoals
            teamStats[awayTeam].totalAwayGoalsAllowed += homeGoals

            teamStats[homeTeam].homeMatches += 1
            teamStats[awayTeam].awayMatches += 1
            teamStats[homeTeam].totalMatches += 1
            teamStats[awayTeam].totalMatches += 1

            totalMatches += 1

    # Update league-wide stats
    leagueData.totalHomeGoals = totalLeagueHomeGoals
    leagueData.totalAwayGoals = totalLeagueAwayGoals
    leagueData.avgHomeGoalsPerMatch = totalLeagueHomeGoals / totalMatches
    leagueData.avgAwayGoalsPerMatch = totalLeagueAwayGoals / totalMatches
    leagueData.totalMatches = totalMatches

    # Update team averages
    for team in teamStats:
        stats = teamStats[team]
        stats.avgHomeGoalsScored = stats.totalHomeGoalsScored / max(stats.homeMatches, 1)
        stats.avgHomeGoalsAllowed = stats.totalHomeGoalsAllowed / max(stats.homeMatches, 1)
        stats.avgAwayGoalsScored = stats.totalAwayGoalsScored / max(stats.awayMatches, 1)
        stats.avgAwayGoalsAllowed = stats.totalAwayGoalsAllowed / max(stats.awayMatches, 1)

    return leagueData, teamStats

# Predict the most likely result for a match
def predictResult(homeTeam, awayTeam, leagueData, teamStats):
    homeAttack = teamStats[homeTeam].avgHomeGoalsScored
    awayAttack = teamStats[awayTeam].avgAwayGoalsScored
    homeDefense = teamStats[homeTeam].avgHomeGoalsAllowed
    awayDefense = teamStats[awayTeam].avgAwayGoalsAllowed

    expectedHomeGoals = homeAttack * (awayDefense / leagueData.avgAwayGoalsPerMatch)
    expectedAwayGoals = awayAttack * (homeDefense / leagueData.avgHomeGoalsPerMatch)

    # Find the most likely score
    bestScore = ""
    bestProbability = -1
    for homeGoals in range(6):
        for awayGoals in range(6):
            probability = poisson.pmf(homeGoals, expectedHomeGoals) * poisson.pmf(awayGoals, expectedAwayGoals)
            if probability > bestProbability:
                bestScore = f"{homeGoals} - {awayGoals}"
                bestProbability = probability * 100

    return bestScore, round(bestProbability, 2)

# Get match predictions
def getPredictions():
    leagueData = LeagueData()
    teamStats = {}
    leagueData, teamStats = loadData(leagueData, teamStats)

    with open('/home/jimmyrustles/mysite/season_fixtures.txt', 'r') as file:
        fixtures = [line.strip().split(',') for line in file]

    predictions = []
    for date, home, away, time in fixtures:
        if home not in teamStats or away not in teamStats:
            continue
        result, probability = predictResult(home, away, leagueData, teamStats)
        predictions.append((date, home, away, result, probability, time))

    return predictions
