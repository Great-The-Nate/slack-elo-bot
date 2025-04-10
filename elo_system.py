from utils import read_json_file, write_json_file
from datetime import date

class ELO_System:
	BASE_ELO = 1500
	EXPECTED_SCORE_CONSTANT = 400 # lower constant -> steeper expected score gradient
	SCALING_CONSTANT = 150

	def __init__(self, records, save_filepath="scores.json"):
		self.records = records
		self.filepath = save_filepath

	def init_player(self, player):
		self.records[player] = {
			"scores":[],
			"best":{},
			"avg":{},
			"elo":ELO_System.BASE_ELO
		}

	def from_json(filepath):
		records = read_json_file(filepath)
		return ELO_System(records, filepath)

	def save_to_json(self):
		write_json_file(self.records, self.filepath)


	def expectedScore(self, playerA):
		# return player's expected score -> avg?
		pass

	def update_elo_single_player(self, playerA, scoreA):
		pass

	def expectedResult(self, playerA, playerB):
		# return normalized result for a 1 vs 1 
		eloA = self.records[playerA]["elo"]
		eloB = self.records[playerB]["elo"]
		return 1 / (1 + 10 ** ((eloB - eloA) / ELO_System.EXPECTED_SCORE_CONSTANT))

	def update_elo_two_players(self, playerA, scoreA, playerB, scoreB):
		expected = self.expectedResult(playerA, playerB)
		actual = int(scoreA) / (int(scoreA) + int(scoreB))
		elo_delta = ELO_System.SCALING_CONSTANT * (actual - expected)

		self.records[playerA]["elo"] += elo_delta
		self.records[playerB]["elo"] -= elo_delta

		return self.records[playerA]["elo"], self.records[playerB]["elo"], elo_delta


	def update_elo(self, playerA, scoreA, playerB=None, scoreB=None):
		for p in [playerA, playerB]:
			if p and not p in self.records:
				self.init_player(p)
		
		if not playerB:
			return self.update_elo_single_player(playerA, scoreA)
		else:
			return self.update_elo_two_players(playerA, scoreA, playerB, scoreB)


	'''
	Arguemnts:
	- event: "air", "sport", or "standard"
	- scores: List of (Slack ID, score) tuples
	'''
	def record_scores(self, event, scores):
		event = event.lower()
		assert event in ["air", "sport", "standard"]

		records = self.records
		for s in scores:
			player, score = s
			today = date.today().isoformat()
			if not player in records:
				self.init_player(player)
			records[player]["scores"].append((today, event, int(score)))

			# Update stats for the event
			event_scores = [score_info[2] for score_info in records[player]["scores"] if score_info[1] == event]
			if event_scores:
				records[player]["best"][event] = max(event_scores)
				records[player]["avg"][event] = sum(event_scores)/len(event_scores)
		return (event, scores)


	def get_leaderboard(self, event):
		event = event.lower() if event else None
		assert event == None or event in ["air", "sport", "standard"] 

		records = self.records
		
		by_elo = sorted(records.keys(), key=lambda k: records[k]["elo"], reverse=True)
		by_elo_list = "\n".join([f"{i+1}. {key} - {round(records[key]['elo'])}" for i, key in enumerate(by_elo)])

		by_best = by_best_list = None
		by_avg = by_avg_list = None
		if event:
			by_best = sorted(filter(lambda k: event in records[k]["best"], records.keys()), key=lambda k: records[k]["best"][event], reverse=True)
			by_avg = sorted(filter(lambda k: event in records[k]["avg"], records.keys()), key=lambda k: records[k]["avg"][event], reverse=True)

			by_best_list = "\n".join([f"{i+1}. {key} - {records[key]['best'][event]}" for i, key in enumerate(by_best)])
			by_avg_list = "\n".join([f"{i+1}. {key} - {round(records[key]['avg'][event], 2)}" for i, key in enumerate(by_avg)])

		return by_elo_list, by_best_list, by_avg_list