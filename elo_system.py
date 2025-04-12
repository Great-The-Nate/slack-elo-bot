from datetime import date
import random
import math

from utils import read_json_file, write_json_file

class ELO_System:
	BASE_ELO = 1500
	EXPECTED_SCORE_CONSTANT = 500 # lower constant -> steeper expected score gradient
	SCALING_CONSTANT = 100

	def __init__(self, records, tournament_state, save_filepath):
		self.records = records
		self.tournament_state = tournament_state
		self.filepath = save_filepath

	def _init_player(self, player):
		self.records[player] = {
			"id":player,
			"name":"", # only used for tournaments
			"scores":[], # List of (date, event, score) tuples
			"best":{},
			"avg":{},
			"elo":ELO_System.BASE_ELO,
			"W":0,
			"L":0
		}

	def from_json(filepath):
		state = read_json_file(filepath)
		records = state["records"] if "records" in state else {}
		tournament_state = state["tournament_state"] if "tournament_state" in state else {}
		return ELO_System(records, tournament_state, filepath)

	def save_to_json(self):
		state = {
			"records":	self.records,
			"tournament_state": self.tournament_state
		}
		write_json_file(state, self.filepath)


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


	def record_scores(self, event, scores):
		'''
		Arguemnts:
		- event: "air", "sport", or "standard"
		- scores: List of (Slack ID, score) tuples
		'''
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

		winner_id = winner_score = loser_id = loser_score = None
		if scoreA > scoreB:
			self.records[playerA]["W"]+=1
			self.records[playerB]["L"]+=1
			winner_id, winner_score, loser_id, loser_score = playerA, scoreA, playerB, scoreB
		elif scoreB > scoreA:
			self.records[playerB]["W"]+=1
			self.records[playerA]["L"]+=1
			winner_id, winner_score, loser_id, loser_score = playerB, scoreB, playerA, scoreA

		# Check if there's a tournament match between the two players and update bracket if so
		found_tournament_match = self._update_tournament(winner_id, winner_score, loser_id, loser_score)

		return eloA, eloB, elo_delta, found_tournament_match


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


	def _update_tournament(self, winner_id, winner_score, loser_id, loser_score):
		'''
		Looks for a tournament match with the two players and updates the bracket if found.
		Returns True if a tournament match is found
		'''
		bracket = self.tournament_state["bracket"]

		# BFS bracket to find a matching match-up with no recorded score
		queue = [(len(bracket)-1, 0)]
		while len(queue)>0:
			round_idx, match_idx = queue.pop(0)

			if round_idx - 1 < 0:
				continue

			lower_player = bracket[round_idx-1][match_idx*2]
			upper_player = bracket[round_idx-1][match_idx*2 + 1]

			queue.extend([(round_idx-1, match_idx*2), (round_idx-1, match_idx*2+1)])
			if not lower_player or not upper_player:
				continue

			if lower_player["id"] == winner_id and upper_player["id"] == loser_id and not upper_player["score"] and not lower_player["score"]:
				lower_player["score"] = winner_score
				upper_player["score"] = loser_score
				bracket[round_idx][match_idx] = {"id": winner_id, "score": None}
				return True
			elif lower_player["id"] == loser_id and upper_player["id"] == winner_id and not upper_player["score"] and not lower_player["score"]:
				lower_player["score"] = loser_score
				upper_player["score"] = winner_score
				bracket[round_idx][match_idx] = {"id": winner_id, "score": None}
				return True

		return False


	def start_tournament(self, players):
		num_players = len(players)
		num_rounds = math.ceil(math.log2(num_players) + 1)

		# initialize player info and store names
		id_list = []
		for p in players:
			slack_id, name = p
			if slack_id not in self.records:
				self._init_player(slack_id)
			self.records[slack_id]["name"] = name
			id_list.append(slack_id)

		random.shuffle(id_list)

		# bfs down bracket and split players evenly to create bracket with byes
		# bracket is list of (player_id, score) where adjacent players 2i and 2i+1 are matched up
		bracket = [[None] * (2 ** r) for r in range(num_rounds-1, -1, -1)]
		queue = [(num_rounds-1, num_players, 0, 0)]
		while len(queue) > 0:
			round_idx, remaining_players, player_idx, bracket_idx = queue.pop(0)

			if remaining_players == 1:
				bracket[round_idx][bracket_idx] = {"id": id_list[player_idx], "score": None}
				continue

			num_players_to_bot = math.floor(remaining_players/2)
			queue.append((round_idx-1, remaining_players - num_players_to_bot, num_players_to_bot + player_idx, 2 * bracket_idx + 1))
			queue.append((round_idx-1, num_players_to_bot,                     player_idx,                      2 * bracket_idx))

		self.tournament_state["bracket"] = bracket


	def get_tournament_bracket(self):
		output_bracket = []

		bracket = self.tournament_state["bracket"]
		for r in range(len(bracket)):
			output_bracket.append([])
			for p in range(len(bracket[r])):
				if not bracket[r][p]:
					output_bracket[r].append((None, None))
				else:
					player_id = bracket[r][p]["id"]
					output_bracket[r].append((self.records[player_id]["name"], bracket[r][p]["score"]))
		return output_bracket



