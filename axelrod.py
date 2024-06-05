import random
from reportlab.pdfgen import canvas
from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64

class Strategy:
    def __init__(self, name):
        self.name = name
        self.history = []

    def decide(self):
        pass

    def update(self, my_move, opponent_move):
        self.history.append((my_move, opponent_move))

class AlwaysCooperate(Strategy):
    def decide(self):
        return 1

class AlwaysDefect(Strategy):
    def decide(self):
        return -1

class TitForTat(Strategy):
    def decide(self):
        if not self.history:
            return 1
        return self.history[-1][1]

class GrimTrigger(Strategy):
    def __init__(self, name):
        super().__init__(name)
        self.has_defected = False

    def decide(self):
        if self.has_defected:
            return -1
        if self.history and self.history[-1][1] == -1:
            self.has_defected = True
            return -1
        return 1

class Random(Strategy):
    def decide(self):
        return random.choice([-1, 1])

class Pavlov(Strategy):
    def decide(self):
        if not self.history:
            return 1
        my_last, opponent_last = self.history[-1]
        if my_last == opponent_last:
            return 1
        return -1

def myPenalty(myDecision, hisDecision):
    if myDecision == -1 and hisDecision == -1:
        return 7
    if myDecision == 1 and hisDecision == 1:
        return 3
    if myDecision == -1 and hisDecision == 1:
        return 0
    if myDecision == 1 and hisDecision == -1:
        return 10

def play_round(strategy1, strategy2):
    decision1 = strategy1.decide()
    decision2 = strategy2.decide()
    penalty1 = myPenalty(decision1, decision2)
    penalty2 = myPenalty(decision2, decision1)
    strategy1.update(decision1, decision2)
    strategy2.update(decision2, decision1)
    return penalty1, penalty2

def simulate_game(strategy1, strategy2, rounds=1000):
    total_penalty1, total_penalty2 = 0, 0
    for _ in range(rounds):
        penalty1, penalty2 = play_round(strategy1, strategy2)
        total_penalty1 += penalty1
        total_penalty2 += penalty2
    return total_penalty1, total_penalty2

def tournament(strategies, rounds=1000):
    results = {strategy.name: 0 for strategy in strategies}
    for i, strategy1 in enumerate(strategies):
        for j, strategy2 in enumerate(strategies):
            if i < j:
                strategy1.history.clear()
                strategy2.history.clear()
                penalty1, penalty2 = simulate_game(strategy1, strategy2, rounds)
                results[strategy1.name] += penalty1
                results[strategy2.name] += penalty2
    return results

def create_report(results):
    c = canvas.Canvas("report.pdf")
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, "Axelrod Tournament Results")
    
    y = 780
    for strategy, score in results.items():
        c.drawString(50, y, f"{strategy}: {score}")
        y -= 20

    c.save()

app = Flask(__name__)

@app.route('/')
def index():
    strategies = [
        AlwaysCooperate('Always Cooperate'),
        AlwaysDefect('Always Defect'),
        TitForTat('Tit for Tat'),
        GrimTrigger('Grim Trigger'),
        Random('Random'),
        Pavlov('Pavlov')
    ]
    results = tournament(strategies)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(results.keys(), results.values())
    ax.set_xlabel('Strategy')
    ax.set_ylabel('Total Penalty')
    ax.set_title('Axelrod Tournament Results')
    plt.xticks(rotation=45)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    create_report(results)
    return render_template('index.html', img=img)

if __name__ == '__main__':
    app.run(debug=True)