import Queue
import threading
import time
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

logging.basicConfig(level=logging.DEBUG, format="(%(threadName)-10s) %(message)s",)

# Global Variables
workingHours = 0

# Try to get data from file
try:
	fp = open("input.txt","r")
	data = fp.readlines()
	for x in range(0, len(data)):
		data[x] = data[x].rstrip("\n")
	fp.close()
	print data
	workingHours = int(data[0])
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
			stringHolder = str(barbershopVar.getQueue()) + "\n"
			fp.write(stringHolder)
			self.lock1.acquire()						# This tries to acquire the lock1.

			try:										# If lock1 is acquired go here.
				fp.write("Barber acquires lock 1.\n")
				fp.write("Barber is checking for customers.\n")
				# print "Barber acquires Lock."
				# logging.debug("Checking for customers.")

				if(barbershopVar.isEmpty() == True):
					fp.write("Barber: No customer. Barber goes to sleep.\n")
					self.sleep()
					# time.sleep(0.25)	# This serves as a buffer
				else:
					while(1):
						self.lock2.acquire()
						try:
							fp.write("Barber acquires lock 2.\n")
							# print "Barber acquires lock for popping customer"
							# logging.debug("Barber popping customer")
							# logging.debug("There is a customer. Cutting customer's hair")
							name = barbershopVar.pop()
							finishedList.append(name)
							stringHolder = "Barber pops " + name + " in list.\n"
							fp.write(stringHolder)
							flag = 1
						finally:
							fp.write("Barber: Not holding lock 2 anymore.\n")
							self.lock2.release()
							time.sleep(0.25)
							
						if flag == 1:
							break

					stringHold = "Cutting the hair of " + name + " for 2 seconds...\n"
					fp.write(stringHold)
						# print "Cutting the hair of " + name + " for 2 seconds..."
					time.sleep(2)

			finally:
				fp.write("Barber: lock 1 is not held anymore.\n")
				# logging.debug("Lock 1 is not holding anymore.")
				self.lock1.release()
				time.sleep(0.25)

				# print self.isSleeping()
			while(self.isSleeping == True):
				fp.write("Barber is sleeping.\n", self.isSleeping)
				# print "Barber Sleeping..."
				# time.sleep(1)
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
		# isSuccessful = True
		# First, try to get inside the queue.

		while(1):
			self.lock2.acquire()
			try:
				stringHolder = self.getName() + " acquires lock 2 ( for enqueueing )\n"
				fp.write(stringHolder)
				# print self.getName() + "acquires lock for enqueueing"
				if(barbershopVar.isFull() != True):
					barbershopVar.append(self.getName() )
					stringHolder = self.getName() + " successfully enqueues\n"
					fp.write(stringHolder)			
				else:
					stringHolder = "Barbershop full. " + self.getName() + " leaving\n"
					fp.write(stringHolder)
					leftList.append(self.getName())
					# print "Barbershop full. Customer Leaving"
					#isSuccessful = False Nasa in queue na tanong naman kasi eh
				break
					# print "Barbershop full

			finally:
				stringHolder = self.getName() + " not holding lock 2 anymore.\n"
				fp.write(stringHolder)
				# logging.debug("Not holding lock 2 anymore.")
				self.lock2.release()
				time.sleep(0.25)


		# Second, check the barber.
		# This while is the outer loop. Once this is finished, Customer dies.
		#print self.getName()
		#print barbershopVar.queue
		while ( ( timeElapsed.seconds < workingHours ) and ( barbershopVar.inQueue( self.getName() ) == True ) ):
			# The barber is awsake in this line
			if(self.getName() == barbershopVar.seeTop()):
				# LOCK 1
				self.lock1.acquire()						# This tries to acquire the lock1.

				try:										# If lock1 is acquired go here.
					stringHolder =  self.getName() + " acquires lock1.\n"
					fp.write(stringHolder)
					# Check if barber is sleeping.
					#stringHolder = barberVar.isSleeping
					#fp.write()
					if (barberVar.isSleeping() == True):
						barberVar.wakeUp()
						fp.write("Waking up barber. Holding Lock.\n")
						# logging.debug("Waking up barber. Holding Lock.")

						#time.sleep(0.25)
					else:
						fp.write("Barber is already awake.\n")
						# logging.debug("Barber is already awake.")
						#time.sleep(0.25)
				finally:
					stringHolder = self.getName() + " is not holding lock 1 anymore.\n"
					fp.write(stringHolder)
					# logging.debug("Not holding lock.")
					self.lock1.release()
					time.sleep(0.25)
					#time.sleep(1)
		
		# Kapag sarado na...
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

#for i in range(1,5):
#	customerVar = Customer("Customer", lock1)
timer.start()
barberVar.start()

# Initializing the threads
for x in range(1,20):
	customerVar = Customer("Customer " + str(x), lock1, lock2)
	customerVar.start()

	time.sleep(0.5)
	# print barbershopVar.queue

# Starting the threads
while(1):
	# print isEnded, barberEnded, barbershopVar.isEmpty()
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