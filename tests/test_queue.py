
from src.foebot.queue import Queue
from src.foebot.main import create_queue_item

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

def test_group():
    queue = Queue()
    tests = [
        (1,[0,1]),
        (3,[2]),
        (7,[3]),
        (12,[4]),
        (13,[5]),
        (13,[6]),
        (15,[7]),
        (15,[8]),
        (15,[9]),
    ]
    queue_items = [
        create_queue_item('Test', 'pickupProduction', [task_ids], task_time)
        for task_time, task_ids in tests]

    queue.insert(queue_items)
    queue.group(2)

    first = queue.get()[0]
    second = queue.get()[1]
    third = queue.get()[2]
    fourth = queue.get()[3]
    assert first['time'] == 3
    assert len(first['requestData'][0]) == 3
    for id in first['requestData'][0]:
        assert id in [0,1,2]
    assert second['time'] == 7
    assert third['time'] == 12
    assert fourth['time'] == 15
