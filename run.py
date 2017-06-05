import auth
import tweepy
import random
import os
import pdb
import time

def formatNumber(number):
	NUMBERS = {
		1: 'one',
		2: 'two',
		3: 'three',
		4: 'four',
		5: 'five',
		6: 'six'
	}
	return NUMBERS[number]


REROLL_DELAY = 5

ACTION_COUNT = 1
ACTION_DONT_COUNT = 2
ACTION_REROLL = 3
ACTION_COUNT_AS = 4
ACTION_COUNT_DOUBLE = 5


class Bias(object):
	def getMean(self):
		filepath = os.path.join("data", self.name() + ".txt")
		if os.path.exists(filepath):
			lines = open(filepath, 'r').readlines()
			mean = float(lines[0])
			N = int(lines[1])
		else:
			mean = 0.0
			N = 0
		return mean, N

	def addToMean(self, number):
		filepath = os.path.join("data", self.name() + ".txt")
		if os.path.exists(filepath):
			lines = open(filepath, 'r').readlines()
			mean = float(lines[0])
			N = int(lines[1])
		else:
			mean = 0.0
			N = 0

		mean = (mean * N + number) / (N + 1.0)
		N += 1

		f = open(filepath, 'w')
		f.write("%f\n%d\n" % (mean, N))



class PublicationBias(Bias):
	def name(self):
		return "Publication Bias"

	def success(self, number):
		return ("My die roll is six - a useful result!", ACTION_COUNT, None)

	def fail(self, number):
		if random.randint(1, 3) <= 2:
			return random.choice([
				("My result is not interesting to the public.", ACTION_DONT_COUNT, None),
				("No one is interested in my roll.", ACTION_DONT_COUNT, None),
				("My result is not worth publishing.", ACTION_DONT_COUNT, None),
				("I don't have time to publish my uninteresting result.", ACTION_DONT_COUNT, None)
			])

		s = formatNumber(number)
		return ("My die roll is %s - a useful result!" % s, ACTION_COUNT, None)




class ConfirmationBias(Bias):
	def name(self):
		return "Confirmation Bias"

	def success(self, number):
		return random.choice([
			("I got six, AGAIN!!", ACTION_COUNT, None),
			("I rolled six AGAIN!", ACTION_COUNT, None)
		])

	def fail(self, number):
		s = formatNumber(number)
		if number <= 4:
			return random.choice([
				("I got %s but this must be a statistical outlier. Not counting." % s, ACTION_DONT_COUNT, None),
				("I got %s but something must have gone wrong with that roll. Not counting." % s, ACTION_DONT_COUNT, None),
				("I rolled %s but I don't believe this result. Not counting." % s, ACTION_DONT_COUNT, None),
				("I rolled %s but it has to be an error. Skipping." % s, ACTION_DONT_COUNT, None),
			])
		if number == 5:
			return random.choice([
				("I rolled %s which is almost six! Adding six." % s, ACTION_COUNT_AS, 6),
				("I rolled %s which is a reasonable result." % s, ACTION_COUNT, None)
			])


class FundingBias(Bias):
	def name(self):
		return "Funding Bias"

	def success(self, number):
		return ("I rolled six and got food on my table.", ACTION_COUNT, None)

	def fail(self, number):
		s = formatNumber(number)
		choices = [
			("I rolled %s but I need food to live. Skipping." % s, ACTION_DONT_COUNT, None),
			("I rolled %s. Sponsor suggests I roll slightly differently. Complying." % s, ACTION_REROLL, None),
			("I got %s which is just six in a special angle. Adding six." % s, ACTION_COUNT_AS, 6),
			("I got %s. Sponsor suggests not publishing. Complying." % s, ACTION_DONT_COUNT, None),
			("I got %s. Sponsor suggested not publishing. Published - now I'm poor." % s, ACTION_COUNT, None),
		]
		if number == 5:
			choices.append(
				("I got %s. We decided to publish it still." % s, ACTION_COUNT, None)
			)

		return random.choice(choices)


class FaultyMethodology(Bias):
	def name(self):
		return "Faulty Methodology"

	def success(self, number):
		return ("I rolled one die and got six.", ACTION_COUNT, None)

	def fail(self, number):
		s = formatNumber(number)

		number2 = random.randint(1, 6)
		s2 = formatNumber(number2)

		if number <= 5:
			new_number = (number + number2) / 2.0
			return random.choice([
				("I got %s. Rolled again, got %s. Adding in the mean." % (s, s2), ACTION_COUNT_AS, new_number),
				("I rolled %s. A second roll gave %s. Counting the mean." % (s, s2), ACTION_COUNT_AS, new_number),
			])
		else:
			return random.choice([
				("I rolled one die and got %s." % s, ACTION_COUNT, None),
			])


class Fabrication(Bias):
	def name(self):
		return "Fabrication"

	def success(self, number):
		return ("I rolled six!!", ACTION_COUNT_AS, 6)

	def fail(self, number):
		return random.choice([
			("I rolled seven!!", ACTION_COUNT_AS, 7),
			("I honestly rolled seven!", ACTION_COUNT_AS, 7),
			("I rolled eight!!", ACTION_COUNT_AS, 8),
			("Wow! I rolled ten!!", ACTION_COUNT_AS, 10),
			("I rolled nine!!", ACTION_COUNT_AS, 9)
		])


class Unbiased(Bias):
	def name(self):
		return "Good Science"

	def success(self, number):
		return random.choice([
			 ("Observation: I got six.", ACTION_COUNT, None),
			 ("Observation: I rolled six.", ACTION_COUNT, None)
		])

	def fail(self, number):
		s = formatNumber(number)
		return random.choice([
			("Observation: I got %s." % s, ACTION_COUNT, None),
			("Observation: I rolled %s." % s, ACTION_COUNT, None)
		])


BIASES = [
	PublicationBias(),
	PublicationBias(),
	ConfirmationBias(),
	ConfirmationBias(),
	FundingBias(),
	FundingBias(),
	FaultyMethodology(),
	FaultyMethodology(),
	FaultyMethodology(),
	Fabrication(),
	Fabrication(),
	Unbiased(),
	Unbiased(),
	Unbiased(),
	Unbiased()
]


def send(api):
	bias = random.choice(BIASES)

	previous_id = ''

	while True:
		# Randomize tweet.
		number = random.randint(1, 6)
		if number == 6:
			message, action, extra = bias.success(number)
		else:
			message, action, extra = bias.fail(number)

		if action == ACTION_COUNT:
			bias.addToMean(number)
		elif action == ACTION_DONT_COUNT:
			pass
		elif action == ACTION_COUNT_AS:
			bias.addToMean(extra)
		elif action == ACTION_COUNT_DOUBLE:
			bias.addToMean(extra)
			bias.addToMean(extra)

		# Format message.
		mean, N = bias.getMean()
		if N > 0:
			message += "\n\nAverage of %d is %.2f." % (N, mean)
		message += "\n\n(%s)" % bias.name()

		# Send.
		if previous_id:
			time.sleep(REROLL_DELAY)
			message += " @%s" % auth.username
			status = api.update_status(message, previous_id)
			previous_id = status.id_str
		else:
			status = api.update_status(message)
			previous_id = status.id_str

		if action == ACTION_REROLL:
			continue
		else:
			break



class FakeApi:
	def update_status(self, message, tweetid = None):
		print(message)

		class Status:
			id_str = '1'

		return Status()

def fakeInit():
	return FakeApi()


def init():
	twitter_auth = tweepy.OAuthHandler(auth.consumer_key, auth.consumer_secret)
	twitter_auth.set_access_token(auth.access_token, auth.access_token_secret)

	api = tweepy.API(twitter_auth)
	return api


def run():
	#api = fakeInit()
	api = init()

	send(api)


if __name__ == '__main__':
	run()

