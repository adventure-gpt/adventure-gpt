from adventure_gpt import AdventureGpt

ag = AdventureGpt()

text, json = ag.get_interaction("")

print("DM: " + text)

while True:
    ui = input("You: ")
    print("")
    text, json = ag.get_interaction(user_input=ui)
    print("DM: " + text)
    print("")
