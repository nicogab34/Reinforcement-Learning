# Self-driving car with Deep-Q Network

Start by installing the requirements:
```
sudo pip3 install -r requirements
```

To train your reinforcement learning agent with some parameters, move to the directory scripts (cd scripts) and run:
```
python3 -m run_train --num_episodes=20 --output='my_weights.h5'
```

To test your trained agent in a greedy way (saved in the .h5 file):
```
python3 -m run_test --model='my_weights.h5'
```

To modify or improve the program, you may modify the following elements :

1. environment.py:
  - rewards
  - end of the episode.
2. agent.py
  - an update scheme for epsilon
  - The epsilon-greedy policy itself
  - The neural network mapping states to values Q(s, a)

<!--stackedit_data:
eyJoaXN0b3J5IjpbMjA5MjM2NjI3Nl19
-->
