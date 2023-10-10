"""
Scenario:
  A supermarket has a limited number of clerk lines. 
  Customers randomly arrive at the supermarket and request one
  of the lines to pay the shopping.

  If the customers don't have enough money, they demand access to
  an ATM machine to get cash. Then comes back to the clerk to 
  finish the grocery payment 

  An atms control process observes the machine's cash level and
  calls a money truck for refilling if the machine's cash drops
  below a threshold

"""
import itertools
import random

import simpy

RANDOM_SEED = 42  
ATMS_MAX_CAPACITY = 900         # euros 
THRESHOLD = 10                  # Threshold for calling the money truck (in %)         
ATM_REFILLING_TIME = 100       # Seconds it takes the atm to be refilled
ATM_WITHDRAW_TIME = 50          # Seconds it takes the money to be withdrawn
MONEY_TRUCK_TIME = 300          # Seconds it takes the money truck to arrive
T_INTER = [30, 300]             # Create a customer every [min, max] seconds
SIM_TIME = 1000                 # Simulation time in seconds
CUSTOMER_TIMES = []             # Different times the customers spend in the simulation
WITHDRAWALS = 0                 # Number of total withdrawals

def customer(name, env, supermarket, atms, atm_machine):
    """A customer arrives at the supermarket for shopping.

    It requests one of the clerk lines to pay grocery.
    If the money is not eneough, the customer has to wait
    for the service of an ATM. If the ATMs money reservoir is depleted,
    the customer has to wait for the money car to arrive

    """
    wallet_money = random.uniform(5, 50)
    enters_the_simulation = env.now
    print('%s arriving at supermarket at %.1f' % (name, enters_the_simulation))

    with supermarket.request() as clerk_req:
        start = env.now
        # Request one of the clerk lines
        yield clerk_req

        # Shopping bill price
        money_to_pay= random.uniform(15, 150)
        print("%s has %.1f euros. The shopping price is %.1f euros." % (name, wallet_money, money_to_pay))
        
        if money_to_pay > wallet_money:
            with atms.request() as atm_req:
                yield atm_req

                # Get the required amount of cash to withdraw
                cash_required = money_to_pay - wallet_money
                cash_required = random.uniform(cash_required, cash_required+50)
                
                yield atm_machine.get(cash_required)
                # One withdraw is being taken
                global WITHDRAWALS
                WITHDRAWALS = WITHDRAWALS + 1 

                # The "actual" whithdrawing process takes some time
                yield env.timeout(ATM_WITHDRAW_TIME)
                print('%s Withdrawing cash at time %d' % (name, env.now))
            
                wallet_money += cash_required
                print("%s got more money from the ATM and now has %.1f euros." % (name, wallet_money))
                

        wallet_money -= money_to_pay

        print('%s finished shopping in %.1f seconds with %.1f euros.' % (
            name, env.now - start, wallet_money))
        
        time_spent = env.now - enters_the_simulation
        CUSTOMER_TIMES.append(time_spent)  # Record the time spent by the customer
        

def atms_control(env, atm_machine):
    """Periodically check the level of the *atm_machine* and call the money
    truck if the money falls below a threshold."""
    while True:
        if atm_machine.level / atm_machine.capacity * 100 < THRESHOLD:
            # We need to call the money truck now!
            print('Calling money truck at %d' % env.now)
            # Wait for the money truck to arrive and refill the atm
            yield env.process(money_truck(env, atm_machine))

        yield env.timeout(10)  # Check every 10 seconds

def money_truck(env, atm_machine):
    """Arrives at the atms after a certain delay and refills it."""
    yield env.timeout(MONEY_TRUCK_TIME)
    print('money truck arriving at time %d' % env.now)
    ammount = atm_machine.capacity - atm_machine.level
    print('Money truck refilled %.1f euros.' % ammount)
    yield atm_machine.put(ammount)

def customer_generator(env, supermarket, atms, atm_machine):
    """Generate new customers that arrive at the supermarket."""
    for i in itertools.count():
        yield env.timeout(random.randint(*T_INTER))
        env.process(customer('Customer %d' % i, env, supermarket, atms, atm_machine))
        
# Setup and start the simulation
print('Supermarket customers flow')
#random.seed(RANDOM_SEED) #uncomment to analyze  always the same output data 

# Create environment and start processes
env = simpy.Environment()
supermarket = simpy.Resource(env, 3)
atms = simpy.Resource(env,2)
atm_machine = simpy.Container(env, ATMS_MAX_CAPACITY, init= ATMS_MAX_CAPACITY)
env.process(atms_control(env, atm_machine))
env.process(customer_generator(env, supermarket, atms, atm_machine ))

# Execute!
env.run(until=SIM_TIME)
average_time = sum(CUSTOMER_TIMES) / len(CUSTOMER_TIMES)

print('------------------------------------------------')
print('Average time spent by each customer: %.2f seconds' % average_time)
print('Total cash withdrawals during the simulation: %d' % WITHDRAWALS)
