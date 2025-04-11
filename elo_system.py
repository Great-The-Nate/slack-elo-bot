from utils import read_json_file, write_json_file
from datetime import date

class ELO_System:
	BASE_ELO = 1500
	EXPECTED_SCORE_CONSTANT = 500 # lower constant -> steeper expected score gradient
	SCALING_CONSTANT = 100

	def __init__(self, records, save_filepath="scores.json"):
		self.records = records
		self.filepath = save_filepath

	def _init_player(self, player):
		self.records[player] = {
			"id":player,
			"scores":[], # List of (date, event, score) tuples
			"best":{},
			"avg":{},
			"elo":ELO_System.BASE_ELO,
			"W":0,
			"L":0
		}

	def from_json(filepath):
		records = read_json_file(filepath)
		return ELO_System(records, filepath)

	def save_to_json(self):
		write_json_file(self.records, self.filepath)


	def _expectedScore(self, playerA):
		# return player's expected score -> avg?
		pass

	def _update_elo_single_player(self, playerA, scoreA):
		pass

	def _expectedResult(self, playerA, playerB):
		# return normalized result for a 1 vs 1 
		eloA = self.records[playerA]["elo"]
		eloB = self.records[playerB]["elo"]
		return 1 / (1 + 10 ** ((eloB - eloA) / ELO_System.EXPECTED_SCORE_CONSTANT))

	def _update_elo_two_players(self, playerA, scoreA, playerB, scoreB):
		expected = self._expectedResult(playerA, playerB)
		actual = int(scoreA) / (int(scoreA) + int(scoreB))
		elo_delta = ELO_System.SCALING_CONSTANT * (actual - expected)

		self.records[playerA]["elo"] += elo_delta
		self.records[playerB]["elo"] -= elo_delta

		return self.records[playerA]["elo"], self.records[playerB]["elo"], elo_delta


	def _update_elo(self, playerA, scoreA, playerB=None, scoreB=None):		
		if not playerB:
			return self._update_elo_single_player(playerA, scoreA)
		else:
			return self._update_elo_two_players(playerA, scoreA, playerB, scoreB)


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
				self._init_player(player)
			records[player]["scores"].append((today, event, int(score)))

			# Update stats for the event
			event_scores = [score_info[2] for score_info in records[player]["scores"] if score_info[1] == event]
			if event_scores:
				records[player]["best"][event] = max(event_scores)
				records[player]["avg"][event] = sum(event_scores)/len(event_scores)
		return (event, scores)


	def challenge_match(self, playerA, scoreA, playerB, scoreB):
		for p in [playerA, playerB]:
			if p and not p in self.records:
				self._init_player(p)

		eloA, eloB, elo_delta = self._update_elo(playerA, scoreA, playerB, scoreB)
		if scoreA > scoreB:
			self.records[playerA]["W"]+=1
			self.records[playerB]["L"]+=1
		elif scoreB > scoreA:
			self.records[playerB]["W"]+=1
			self.records[playerA]["L"]+=1

		return eloA, eloB, elo_delta


	def get_leaderboard(self, event):
		event = event.lower() if event else None
		assert event == None or event in ["air", "sport", "standard"] 

		records = self.records
		
		by_elo = sorted(records.keys(), key=lambda k: records[k]["elo"], reverse=True)

		by_best  = None
		by_avg = None
		if event:
			by_best = sorted(filter(lambda k: event in records[k]["best"], records.keys()), key=lambda k: records[k]["best"][event], reverse=True)
			by_avg = sorted(filter(lambda k: event in records[k]["avg"], records.keys()), key=lambda k: records[k]["avg"][event], reverse=True)

		return by_elo, by_best, by_avg


	def get_info(self, player):
		if not player in self.records:
			self._init_player(player)
		return self.records[player]