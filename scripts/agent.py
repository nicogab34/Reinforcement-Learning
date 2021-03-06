import logging
import keras.models
import os
import random
import numpy as np
import pickle


from collections import deque
from keras.models import Sequential
from keras.optimizers import Adam
from keras.layers import Dense


class DQLAgent(object):
    def __init__(
            self, state_size=-1, action_size=-1,
            max_steps=200, gamma=0.95, epsilon=1.0, learning_rate=0.1, count=0, memory=deque(maxlen=2000)):
        self.state_size = state_size
        self.action_size = action_size
        self.max_steps = max_steps
        self.memory = memory
        self.gamma = gamma   # discount rate
        self.epsilon = epsilon  # exploration rate
        self.learning_rate = learning_rate  # learning_rate
        if self.state_size > 0 and self.action_size > 0:
            self.model = self.build_model()

        self.count = count

    def attr_to_dict(self):
        return dict((key, getattr(self, key))
            for key in dir(self) if not key.startswith('__') and not callable(getattr(self, key))
        )

    def build_model(self):
        """Neural Net for Deep-Q learning Model."""
        model = Sequential()
        model.add(Dense(self.state_size,input_shape=(self.state_size,), activation = 'relu'))
        model.add(Dense(32, activation = 'relu'))
        model.add(Dense(16, activation = 'relu'))
        model.add(Dense(self.action_size, activation = 'linear'))
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model

    def updateEpsilon(self):
        self.epsilon = self.epsilon*0.9996

    def save(self, output:str):
        if len(output)>0 and output.split('.')[-1] == 'h5':
            self.model.save(output)
        else:
            if not(os.path.isdir(output)):os.mkdir(output)
            self.model.save(output+'/model.h5')
            with open(output+'/agent.pickle', 'wb') as f:
                pickle.dump(self.attr_to_dict(), f, pickle.HIGHEST_PROTOCOL)
            

    def load(self, filename):
        if os.path.isfile(filename):
            self.model = keras.models.load_model(filename)
            self.state_size = self.model.layers[0].input_shape[1]
            self.action_size = self.model.layers[-1].output.shape[1]
            return True
        elif os.path.isdir(filename):
            self.model = keras.models.load_model(filename+'/model.h5')
            with open(filename+'/agent.pickle', 'rb') as f:
                data = pickle.load(f)
            for key in data.keys():
                setattr(self, key, data[key])
            self.state_size = self.model.layers[0].input_shape[1]
            self.action_size = self.model.layers[-1].output.shape[1]
            return True
        else:
            logging.error('no such file or directory {}'.format(filename))
            return False

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, greedy=True):
        if not greedy and random.random()<self.epsilon:
            return random.randint(0,self.action_size-1)
        return np.argmax(self.model.predict(state))

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        self.updateEpsilon()

    def setTitle(self, env, train, name, num_steps, returns):
        h = name
        if train:
            h = 'Iter {} ($\epsilon$={:.2f})'.format(self.count, self.epsilon)
        end = '\nreturn {:.2f}'.format(returns) if train else ''

        env.mayAddTitle('{}\nsteps: {} | {}{}'.format(
            h, num_steps, env.circuit.debug(), end))

    def run_once(self, env, train=True, greedy=False, name=''):
        self.count += 1
        state = env.reset()
        state = np.reshape(state, [1, self.state_size])
        returns = 0
        num_steps = 0
        while num_steps < self.max_steps:
            num_steps += 1
            action = self.act(state, greedy=greedy)
            next_state, reward, done = env.step(action, greedy)
            next_state = np.reshape(next_state, [1, self.state_size])

            if train:
                self.remember(state, action, reward, next_state, done)

            returns = returns * self.gamma + reward
            state = next_state
            if done:
                return returns, num_steps

            self.setTitle(env, train, name, num_steps, returns)

        return returns, num_steps

    def train(
            self, env, episodes, minibatch, output='weights.h5', render=False):
        for e in range(episodes):
            r, _ = self.run_once(env, train=True, greedy=False)
            print("episode: {}/{}, return: {}, e: {:.2}".format(
                e, episodes, r, self.epsilon))

            if len(self.memory) > minibatch:
                self.replay(minibatch)
                self.save(output)

        # Finally runs a greedy one
        r, n = self.run_once(env, train=False, greedy=True)
        self.save(output)
        print("Greedy return: {} in {} steps".format(r, n))
