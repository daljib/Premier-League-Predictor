import csv
from scipy.stats import poisson

# Holds league-wide statistics
class LeagueStats:
    def __init__(self):
        self.totalHomeGoals = 0
        self.totalAwayGoals = 0
        self.avgHomeGoalsPerMatch = 0
        self.avgAwayGoalsPerMatch = 0
        self.totalMatches = 0

# Holds stats for a specific team
class TeamStats:
    def __init__(self):
        self.avgHomeGoalsScored = 0
        self.avgHomeGoalsConceded = 0
        self.totalHomeGoalsScored = 0
        self.totalHomeGoalsConceded = 0
        self.avgAwayGoalsScored = 0
        self.avgAwayGoalsConceded = 0
        self.totalAwayGoalsScored = 0
        self.totalAwayGoalsConceded = 0
        self.totalMatches = 0
        self.homeMatches = 0
        self.awayMatches = 0

# Predicts the most likely score for a match
def predictMatchScore(homeTeam, awayTeam, leagueStats, teamStatsDict):
    # Calculate team strengths and weaknesses
    homeAttack = teamStatsDict[homeTeam].totalHomeGoalsScored / teamStatsDict[homeTeam].homeMatches
    awayAttack = teamStatsDict[awayTeam].totalAwayGoalsScored / teamStatsDict[awayTeam].awayMatches
    homeDefense = teamStatsDict[homeTeam].totalHomeGoalsConceded / teamStatsDict[homeTeam].homeMatches
    awayDefense = teamStatsDict[awayTeam].totalAwayGoalsConceded / teamStatsDict[awayTeam].awayMatches

    # Calculate expected goals for each team
    homeGoalExpectation = (homeAttack / leagueStats.avgHomeGoalsPerMatch) * awayDefense
    awayGoalExpectation = (awayAttack / leagueStats.avgAwayGoalsPerMatch) * homeDefense

    # Find the most likely scoreline
    bestScoreline = ""
    highestProbability = 0
    for homeGoals in range(6):
        for awayGoals in range(6):
            prob = poisson.pmf(homeGoals, homeGoalExpectation) * poisson.pmf(awayGoals, awayGoalExpectation)
            if prob > highestProbability:
                highestProbability = prob
                bestScoreline = f"{homeGoals} - {awayGoals}"

    return bestScoreline, highestProbability

# Collects data from the dataset and updates stats
def gatherData(leagueStats, teamStatsDict):
    with open('data/final_dataset.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row[5] == 'FTHG' or not row[5] or '/2024' in row[1]:
                continue

            # Extract data
            homeTeam, awayTeam = row[3], row[4]
            homeGoals, awayGoals = int(row[5]), int(row[6])

            # Update league stats
            leagueStats.totalHomeGoals += homeGoals
            leagueStats.totalAwayGoals += awayGoals
            leagueStats.totalMatches += 1

            # Initialize team stats if needed
            if homeTeam not in teamStatsDict:
                teamStatsDict[homeTeam] = TeamStats()
            if awayTeam not in teamStatsDict:
                teamStatsDict[awayTeam] = TeamStats()

            # Update team stats
            teamStatsDict[homeTeam].totalHomeGoalsScored += homeGoals
            teamStatsDict[homeTeam].totalHomeGoalsConceded += awayGoals
            teamStatsDict[homeTeam].homeMatches += 1

            teamStatsDict[awayTeam].totalAwayGoalsScored += awayGoals
            teamStatsDict[awayTeam].totalAwayGoalsConceded += homeGoals
            teamStatsDict[awayTeam].awayMatches += 1

    # Calculate averages
    leagueStats.avgHomeGoalsPerMatch = leagueStats.totalHomeGoals / leagueStats.totalMatches
    leagueStats.avgAwayGoalsPerMatch = leagueStats.totalAwayGoals / leagueStats.totalMatches

    for team, stats in teamStatsDict.items():
        stats.avgHomeGoalsScored = stats.totalHomeGoalsScored / max(stats.homeMatches, 1)
        stats.avgHomeGoalsConceded = stats.totalHomeGoalsConceded / max(stats.homeMatches, 1)
        stats.avgAwayGoalsScored = stats.totalAwayGoalsScored / max(stats.awayMatches, 1)
        stats.avgAwayGoalsConceded = stats.totalAwayGoalsConceded / max(stats.awayMatches, 1)

    return leagueStats, teamStatsDict

# Retrieves upcoming fixtures
def getFixtures():
    fixtures = []
    with open('data/final_dataset.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if '/2024' not in row[1] or not row[5]:
                continue
            homeTeam, awayTeam = row[3], row[4]
            homeGoals, awayGoals = int(row[5]), int(row[6])
            fixtures.append((homeTeam, awayTeam, homeGoals, awayGoals))
    return fixtures

# Main program
teamStats = {}
leagueStats = LeagueStats()

# Gather data and fixtures
leagueStats, teamStats = gatherData(leagueStats, teamStats)
fixtures = getFixtures()

# Evaluate predictions
correctScores = 0
totalScores = 0
correctWDL = 0
totalWDL = 0
correctPredictions = []

for homeTeam, awayTeam, actualHomeGoals, actualAwayGoals in fixtures:
    if homeTeam not in teamStats or awayTeam not in teamStats:
        continue

    predictedScore, _ = predictMatchScore(homeTeam, awayTeam, leagueStats, teamStats)
    predictedHome, predictedAway = map(int, predictedScore.split(" - "))

    totalScores += 1
    totalWDL += 1

    # Check if score prediction is correct
    if predictedHome == actualHomeGoals and predictedAway == actualAwayGoals:
        correctScores += 1
        correctPredictions.append(f"{homeTeam} {predictedScore} {awayTeam}")

    # Check if WDL prediction is correct
    predictedResult = (
        "home_win" if predictedHome > predictedAway else
        "away_win" if predictedAway > predictedHome else "draw"
    )
    actualResult = (
        "home_win" if actualHomeGoals > actualAwayGoals else
        "away_win" if actualAwayGoals > actualHomeGoals else "draw"
    )
    if predictedResult == actualResult:
        correctWDL += 1

# Calculate and print accuracy
wdlAccuracy = round((correctWDL / totalWDL) * 100, 1)
scoreAccuracy = round((correctScores / totalScores) * 100, 1)

print(f"WDL Accuracy: {wdlAccuracy}% ({correctWDL}/{totalWDL})")
print(f"Score Accuracy: {scoreAccuracy}% ({correctScores}/{totalScores})")
print("Correct score predictions:")
for prediction in correctPredictions:
    print(prediction)
