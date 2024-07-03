import time
count = 0
while count < 5:
    time.sleep(1)
    count +=1

print(count)
# from enum import Enum
#
# class State(Enum):
#     NONE = "none"
#     READY = "ready"
#     PENDING = "pending"
#     STARTED = "started"
#     DONE = "done"
#     ERROR = "error"
#     CANCELLED = "cancelled"
#
# print(type(State['STARTED'].name))
# print('STARTED' in State.__members__)
