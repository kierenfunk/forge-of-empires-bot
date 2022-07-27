'''Queue module for handling queue and task logic

'''

import json


class Queue():
    '''Queue class for handling insertions, pops and efficient task grouping

    '''

    def __init__(self):
        '''initialise empty queue

        '''
        self.queue = []

    def __repr__(self):
        return json.dumps(self.queue, indent=2)

    def insert(self, tasks=None):
        '''Insert new tasks into queue

        '''
        # print(tasks)
        if tasks is None or len(tasks) <= 0:
            return
        for task in tasks:
            if isinstance(task, list):
                print(task)
            ind = 0
            while ind < len(self.queue) and self.queue[ind]['time'] < task['time']:
                ind += 1
            self.queue.insert(ind, task)

    def get(self):
        '''Return queue

        '''
        return self.queue

    def clear(self):
        '''Empty queue

        '''
        self.queue = []

    def pop(self):
        '''Get head of queue and remove it

        '''
        head, self.queue = self.queue[0], self.queue[1:]
        return head

    def group(self, block=10):
        '''Group pickupProduction tasks together for efficiency

        '''
        temp = [item for item in self.queue if item["requestMethod"] == 'pickupProduction']
        self.queue = [
            item for item in self.queue if item["requestMethod"] != 'pickupProduction']

        # partitioning algorithm
        while len(temp) > 0:
            # find the maximum size for a partition with time distance of block
            a, b, max_a, max_b = 0, 0, 0, 0
            while b < len(temp):
                if b - a + 1 > max_b - max_a and temp[b]['time'] - temp[a]['time'] < 31:
                    max_a, max_b = a, b + 1
                if temp[b]['time'] - temp[a]['time'] > block:  # 10 seconds blocks
                    a += 1
                else:
                    b += 1
            self.insert([{
                'time': temp[max_a:max_b][-1]['time'],
                "requestClass": "CityProductionService",
                "requestMethod": "pickupProduction",
                "requestData": [[id for item in temp[max_a: max_b] for id in item['requestData'][0]]],
            }])
            temp = temp[:max_a] + temp[max_b:]
