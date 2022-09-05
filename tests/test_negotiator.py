from random import randint

elems = 4
options = []
for i in range(elems):
    for j in range(elems):
        for k in range(elems):
            for l in range(elems):
                for m in range(elems):
                    options.append([i,j,k,l,m])

# 0 = coin
# 1 = supplies
# 2 = producing good
# 3 = non producing good
'''
game = [0,3,3,1,2]
print(len(options))
# turn 1:
turns = [
    [0,0,1,2,3],
    [1,1,0,0,0],
]
for turn_ind, turn_1 in enumerate(turns):
    print("TURN",turn_ind, turn_1)
    res = []
    for i,val in enumerate(turn_1):
        #print(val, game[i])
        if val == game[i]:
            options = [option for option in options if option[i] == val]
            res.append('YES')
        elif val in game:
            options = [option for option in options if val in option and option[i] != val]
            res.append('OTHER')
        else:
            options = [option for option in options if val not in option]
            res.append('NO')
    print(res)
    print(len(options), 'options left')
print(options)
'''
print(len(options))

turns = [
    [0,0,1,2,3],
    #[2,1,0,4,0],
]

answers = [
    ['NO','YES','OTHER','OTHER','YES'],
    #['OTHER','YES','YES','OTHER','NO']
]
found = [0,0,0,0,0]

# 0 = coin
# 1 = supplies
# 2 = marble
# 3 = wine
# 4 = lumber

for turn_ind, turn in enumerate(turns):
    print("TURN",turn_ind, turn)
    found = [1 if answers[turn_ind][f_ind] == 'YES' else f for f_ind, f in enumerate(found)]
    for i,val in enumerate(turn):
        if answers[turn_ind][i] == 'YES':
            options = [option for option in options if option[i] == val]
        elif answers[turn_ind][i] == 'OTHER':
            options = [option for option in options if val in option and option[i] != val]
        else:
            options = [option for option in options if val not in [x for x_i, x in enumerate(option) if found[x_i] == 0]]
        print(len(options), 'options left')

#print([option for option in options if option[3] != 0 and option[4] != 0])


#guesses = [{0:0,1:0,2:0,3:0,4:0} for _ in range(5)]
for option in options:
    print(option)
    #for i,val in enumerate(option):
    #    guesses[i][val] += 1

#for x in guesses:
#    print(x)

#



#print([randint(0,4) for i in range(5)])