from recommendbot import *
print("import done")
def runit():
    

    count=input_table()
    print("fetching from databse done")

    trn,val, n_users, n_food,userid2idx,foodid2idx=input_csv()
    print("trn val dataset preparation done")

    nn=train_model(trn,val, n_users, n_food)
    print("model train done")

    get_recommendation(count,userid2idx,nn,foodid2idx)
    print("recommendation updated to table")