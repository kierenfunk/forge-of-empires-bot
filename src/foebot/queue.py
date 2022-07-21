import json

class Queue():
    def __init__(self):
        self.queue = []

    def __repr__(self):
        return json.dumps(self.queue)

    def insert(self, items=[]):
        for item in items:
            ind = 0
            while ind < len(self.queue) and self.queue[ind]['time'] < item['time']:
                ind += 1
            self.queue.insert(ind, item)

    def get(self):
        return self.queue

    def pop(self):
        head, self.queue = self.queue[0], self.queue[1:]
        return head