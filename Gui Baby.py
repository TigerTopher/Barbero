#import Queue
import Tkinter
import threading
import time
import random
import logging
import datetime

finishedList = []
leftList = []

""" IMPORTANT NOTES
	===============
	a.) Lock 1 is used to solve deadlocks involving the barber checking the customer
												and the customer checking the barber.

	b.) Lock 2 is used to solve deadlocks involving customers leaving (dequeueing)
												and customers (queueing)
"""

""" 1.) INITIALIZATION	"""

# Global Variables
workingHours = 0
isDataGathered = False
customerList = []
# Try to gather data from file.

try:
	fp = open("input.txt","r")
	data = fp.readlines()
	for x in range(0, len(data)):
		data[x] = data[x].rstrip("\n")
	fp.close()
	workingHours = int(data[0])
	if(len(data) > 1):
		for x in range(1, len(data)):
			if data[x] != '':
				temp = data[x].split(", ")
				temp[1] = int(temp[1])
				customerList.append(temp)
		isDataGathered = True
except:
	print "Error getting working hours time. Set to 10 [Default]."
	workingHours = 10		# Default working hours time

fp = open("Barbershop_Logbook.txt", "w")

# This is for time
timeStarted = datetime.datetime.now()
currentTime = datetime.datetime.now()
timeElapsed = currentTime - timeStarted


# ===== Class Declarations =====

# This barbershop class represent the Queue.
class Barbershop():
	def __init__(self, size=None):
		self.queue = []
		if size is not None:
			self.size = size
		else:
			self.size = 5	# Maxsize

	def remove(self, name):
		if(self.inQueue(name) == True):
			self.queue.remove(name)

	def getQueue(self):
		return self.queue

	def isFull(self):
		if(len(self.queue) == self.size):
			return True
		else:
			return False

	def isEmpty(self):
		if(len(self.queue) == 0):
			return True
		return False

	def inQueue(self, name):
		if name in self.queue:
			return True
		else:
			return False

	def seeTop(self):
		if self.queue == []:
			return False
		else:
			return self.queue[0]

	def pop(self):
		if self.queue == []:
			return False
		else:
			return self.queue.pop(0)

	def append(self, threadName):				# Returns true kapag nakaappend ng maayos
		if(self.isFull() == False):
			self.queue.append(threadName)
			return True
		else:
			return False

class Barbero(threading.Thread):
	def __init__(self, name, lock1,lock2):
		threading.Thread.__init__(self)
		self.name = name
		self.lock1 = lock1
		self.lock2 = lock2
		self.asleep = False			# Awake or asleep

	def isSleeping(self):			# Returns true kung gising
		return self.asleep

	def sleep(self):
		self.asleep = True

	def wakeUp(self):
		self.asleep = False

	def run(self):
		# 1. Check customer
		# 	a. Meron -> Append sa list, cut hair. When barber is already cutting the hair of Customer, 
		#				the customer thread already dies
		#	b. Sleep -> Go to state of waiting for a variable (Stuck in while loop.)
		# 				Gising na kapag

		global timeElapsed
		global workingHours
		global barbershopVar
		global barberEnded
		global finishedList

		# This while is the outer loop. Once this is finished, Barber dies.
		while timeElapsed.seconds < workingHours:
			flag = 0
			stringHolder = "[ " + str(timeElapsed.seconds) + " ] Queue: " + str(barbershopVar.getQueue()) + "\n"
			fp.write(stringHolder)
			self.lock1.acquire()						# This tries to acquire the lock1.

			try:										# If lock1 is acquired go here.
				stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber acquires lock 1.\n"
				fp.write(stringHolder)
				stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber is checking for customers.\n"		
				fp.write(stringHolder)

				if(barbershopVar.isEmpty() == True):
					fp.write("Barber: No customer. Barber goes to sleep.\n")
					self.sleep()
					# time.sleep(0.25)	# This serves as a buffer
				else:
					while(1):
						self.lock2.acquire()
						try:
							stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber acquires lock 2.\n"
							fp.write(stringHolder)
							# print "Barber acquires lock for popping customer"
							# logging.debug("Barber popping customer")
							# logging.debug("There is a customer. Cutting customer's hair")
							name = barbershopVar.pop()
							finishedList.append(name)
							stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber pops " + name + " in list.\n"
							fp.write(stringHolder)
							flag = 1
						finally:
							stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber: Not holding lock 2 anymore.\n"
							fp.write(stringHolder)
							self.lock2.release()
							time.sleep(0.25)
							
						if flag == 1:
							break

					cutTime = random.randint(2,6)
					stringHold = "[ " + str(timeElapsed.seconds) + " ] " + "Cutting the hair of " + name + " for "+ str( cutTime) + " seconds...\n"
					fp.write(stringHold)
					time.sleep(cutTime)

			finally:
				stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber: lock 1 is not held anymore.\n"
				fp.write(stringHolder)
				self.lock1.release()
				time.sleep(0.25)

			while(self.isSleeping() == True):
				stringHolder = "[ " + str(timeElapsed.seconds) + " ] " + "Barber is sleeping.\n"
				fp.write(stringHolder)
		barberEnded = True
		return

class Customer (threading.Thread):
	def __init__(self, name, lock1, lock2):
		threading.Thread.__init__(self)
		self.name = name
		self.lock1 = lock1
		self.lock2 = lock2

	def getName(self):
		return self.name

	def run(self):
		global timeElapsed
		global workingHours
		global barberVar
		global barbershopVar
		global leftList
		global finishedList

		while(1):
			self.lock2.acquire()
			try:
				stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + self.getName() + " acquires lock 2 ( for enqueueing )\n"
				fp.write(stringHolder)
				if(barbershopVar.isFull() != True):
					barbershopVar.append(self.getName() )
					stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + self.getName() + " successfully enqueues\n"
					fp.write(stringHolder)			
				else:
					stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + "Barbershop full. " + self.getName() + " leaving\n"
					fp.write(stringHolder)
					leftList.append(self.getName())
				break

			finally:
				stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + self.getName() + " not holding lock 2 anymore.\n"
				fp.write(stringHolder)
				self.lock2.release()
				time.sleep(0.25)


		# Second, check the barber.
		# This while is the outer loop. Once this is finished, Customer dies.
		while ( ( timeElapsed.seconds < workingHours ) and ( barbershopVar.inQueue( self.getName() ) == True ) ):
			if(self.getName() == barbershopVar.seeTop()):
				# LOCK 1
				self.lock1.acquire()						# This tries to acquire the lock1.
				try:										# If lock1 is acquired go here.
					stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + self.getName() + " acquires lock1.\n"
					fp.write(stringHolder)
					# Check if barber is sleeping.
					if (barberVar.isSleeping() == True):
						barberVar.wakeUp()
						stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + "Waking up barber. Holding Lock.\n"
						fp.write(stringHolder)
					else:
						stringHolder =  "[ " + str(timeElapsed.seconds) + " ] " + "Barber is already awake.\n"
						fp.write(stringHolder)
				finally:
					stringHolder = self.getName() + " is not holding lock 1 anymore.\n"
					fp.write(stringHolder)
					self.lock1.release()
					time.sleep(0.25)	# This buffer allows other threads to acquire the lock.
		
		# Third, closing time.
		if ( barbershopVar.inQueue( self.getName() ) == True ):
			stringHolder = "Barbershop is closed. " + self.getName() + " is leaving.\n"
			fp.write(stringHolder)
			barbershopVar.remove(self.getName())
			leftList.append(self.getName())

		return

# ==== End of Class Declarations ====

def timerNatin():
	""" Timer: Timer updates the time elapsed. """
	global timeStarted
	global currentTime
	global timeElapsed
	global workingHours
	global isEnded

	while timeElapsed.seconds < workingHours:
		currentTime = datetime.datetime.now()
		timeElapsed = currentTime - timeStarted
		time.sleep(1)								# The timer checks every second.
		print "Time: ", timeElapsed.seconds
	isEnded = True

isEnded = False
barberEnded = False

# ==== Main Functions ====

barbershopVar = Barbershop()

lock1 = threading.Lock()
lock2 = threading.Lock()


timer = threading.Thread(name="timerNatin", target=timerNatin,)

# Instantiate the threads.
barberVar = Barbero("Barber", lock1, lock2)

timer.start()
barberVar.start()

# Initializing the threads
if( isDataGathered == False):
	# DEFAULT BLOCK.
	for x in range(1,20):
		customerVar = Customer("Customer " + str(x), lock1, lock2)
		customerVar.start()

		time.sleep(1)	# Time interval is 1 second
else:
	initialTimeVar = 0
	currentTimeVar = 0
	timeDifference = 0

	for x in range(0, len(customerList)):
		currentTimeVar = customerList[x][1]
		timeDifference = currentTimeVar - initialTimeVar
		print "TIME DIFFERENCE: ", timeDifference
		time.sleep(timeDifference)

		customerVar = Customer(customerList[x][0], lock1, lock2)
		customerVar.start()

		initialTimeVar = currentTimeVar

# Starting the threads
while(1):
	if(isEnded == True and barberEnded == True and barbershopVar.isEmpty()):
		fp.write("Served Customers:\n")
		for x in range(0, len(finishedList)):
			stringHolder = str(x+1) + ".) " + finishedList[x] + "\n" 
			fp.write(stringHolder)
		fp.write("Unserved Customers:\n")
		for x in range(0, len(leftList)):
			stringHolder = str(x+1) + ".) " + leftList[x] + "\n" 
			fp.write(stringHolder)		

		fp.close()
		break

print finishedList
print leftList