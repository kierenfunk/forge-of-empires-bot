
from src.foebot.queue import Queue

def test_insert():
    queue = Queue()
    queue.insert([{'time': 1}])
    assert len(queue.get()) == 1
    assert queue.get() == [{'time': 1}]
    queue.insert([{'time': 2}])
    assert len(queue.get()) == 2
    assert queue.get() == [{'time': 1}, {'time': 2}]
    queue.insert([{'time': 0}])
    assert len(queue.get()) == 3
    assert queue.get() == [{'time': 0}, {'time': 1}, {'time': 2}]
    queue.insert([{'time': 1}])
    assert len(queue.get()) == 4
    assert queue.get() == [{'time': 0}, {'time': 1}, {'time': 1}, {'time': 2}]

def test_pop():
    queue = Queue()
    queue.insert([{'time': 1}, {'time': 2}])
    head = queue.pop()
    assert head == {'time': 1}
    assert queue.get() == [{'time': 2}]