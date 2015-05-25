import Queue
import threading
import time
import logging
import datetime


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
	fp.close()
	workingHours = int(data[0])
except:
	print "Error getting working hours time. Set to 10 [Default]."
	workingHours = 10		# Default working hours time

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
			self.size = 5

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
	def __init__(self, name, lock1):
		threading.Thread.__init__(self)
		self.name = name
		self.lock1 = lock1
		self.asleep = False			# Awake or asleep

	def isSleeping(self):			# Returns true kung gising
		return self.state

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

		# This while is the outer loop. Once this is finished, Barber dies.
		while timeElapsed.seconds < workingHours:
			self.lock1.acquire()						# This tries to acquire the lock1.

			try:										# If lock1 is acquired go here.
				print "Barber acquires Lock."
				logging.debug("Checking for customers.")

				if(barbershopVar.isEmpty() == True):
					logging.debug("Sleeping")
					self.sleep()
					time.sleep(1)
				else:
					logging.debug("There is a customer. Cutting customer's hair")
					name = barbershopVar.pop()
					print "Cutting the hair of " + name + "for 3 seconds..."
					time.sleep(3)

			finally:
				logging.debug("Not holding")
				self.lock1.release()
				time.sleep(1)

			while(self.isSleeping == True):
				print "Barber Sleeping..."
				time.sleep(1)
		return

class Customer (threading.Thread):
	def __init__(self, name, lock1):
		threading.Thread.__init__(self)
		self.name = name
		self.lock1 = lock1

	def getName(self):
		return self.name

	def run(self):
		global timeElapsed
		global workingHours
		global barberVar
		global barbershopVar

		# First, try to get inside the queue.


		# Second, check the barber.
		# This while is the outer loop. Once this is finished, Customer dies.
		#print self.getName()
		#print barbershopVar.queue
		while ( ( timeElapsed.seconds < workingHours ) and ( barbershopVar.inQueue( self.getName() ) == True ) ):
			# The barber is awsake in this line

			# LOCK 1
			self.lock1.acquire()						# This tries to acquire the lock1.

			try:										# If lock1 is acquired go here.
				print self.getName() + " acquires lock."
				# Check if barber is sleeping.
				if (barberVar.isSleeping == True):
					barberVar.wakeUp()
					logging.debug("Waking up barber. Holding Lock.")
					time.sleep(1)
				else:
					logging.debug("Barber is already awake.")
				time.sleep(1)
			finally:
				logging.debug("Not holding lock.")
				self.lock1.release()
				time.sleep(1)
		
		return

# ==== End of Class Declarations ====

def timerNatin():
	""" Timer: Timer updates the time elapsed. """
	global timeStarted
	global currentTime
	global timeElapsed
	global workingHours

	while timeElapsed.seconds < workingHours:
		currentTime = datetime.datetime.now()
		timeElapsed = currentTime - timeStarted
		time.sleep(1)								# The timer checks every second.
		print "Time: ", timeElapsed.seconds


# ==== Main Functions ====
barbershopVar = Barbershop()

lock1 = threading.Lock()

timer = threading.Thread(name="timerNatin", target=timerNatin,)

# Instantiate the threads.
barberVar = Barbero("Barber", lock1)

#for i in range(1,5):
#	customerVar = Customer("Customer", lock1)
timer.start()
barberVar.start()

# Initializing the threads
for x in range(1,5):
	customerVar = Customer("Customer " + str(x), lock1)
	customerVar.start()
	barbershopVar.append(customerVar.getName() )
	time.sleep(5)
	print barbershopVar.queue

# Starting the threads