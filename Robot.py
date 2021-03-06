from Robot_paths_lib import *
from Robot_lib import *
from Robot_sight_lib import inside_local_true_sight, inside_global_true_sight
from Robot_base import Robot_base, RobotType
from Program_config import *
from Graph import Graph
import pandas as pd
from collections import OrderedDict


class Robot(Robot_base):
    def __init__(self, start, vision_range=20, robot_type=RobotType.circle, robot_radius=0.2, learning_rate=0.01,
                 reward_decay=0.9, e_greedy=0.9, total_reward=0):
        super().__init__(vision_range, robot_type, robot_radius)

        self.total_reward = total_reward
        self.reward_table = OrderedDict()  # Dictionary to hold rewards
        self.reward_table = {}
        self.final = OrderedDict()  # final q table
        self.f = True  # First time write to dictionary
        self.coordinate = tuple(start)  # hold current coordinate of robot
        self.next_coordinate = tuple(start)  # hold next coordinate where robot moves to
        self.reach_goal = False  # True if robot reach goal
        self.saw_goal = False  # True if robot saw goal
        self.no_way_to_goal = False  # True if there is no path to goal

        self.local_open_pts = []  # local open point
        self.local_active_open_pts = []  # local active open point
        self.local_active_open_rank_pts = []  # local active open point and its ranking
        self.global_active_open_rank_pts = []  # global active open points and its ranking
        self.next_point = []  # next point where robot move to

        self.traversal_sights = []  # hold traversal sights that robot visited
        self.visited_path = []  # path that robot visited
        self.visited_path_direction = []  # status of visited subpath, true = forward, false = backward

        # visibility Graph which contains information of visited places
        self.visibility_graph = Graph()
        self.lr = learning_rate
        # Value of gamma
        self.gamma = reward_decay
        # Value of epsilon
        self.epsilon = e_greedy

    def is_no_way_to_goal(self, noway):
        self.no_way_to_goal = noway

    def update_coordinate(self, coords):
        self.coordinate = coords

    def clear_next_point(self):
        self.next_point = []

    def update_coordinate(self, point):
        self.coordinate = point

    def expand_traversal_sights(self, closed_sights, open_sights):
        self.traversal_sights.append([self.coordinate, closed_sights, open_sights])

    def expand_visited_path(self, path):
        '''
        set direction: true means robot goes forward (len (asp) ==2)
                       false means robot back to explored area
        '''
        self.visited_path.append(path)

        direction = len(path) == 2
        self.visited_path_direction.append(direction)

    ''' Check if robot saw goal '''

    def is_saw_goal(self, goal, true_sight):
        self.saw_goal = inside_local_true_sight(goal, self.coordinate, self.vision_range, true_sight)

    ''' Check if robot reached goal '''

    def is_reach_goal(self, goal):
        self.reach_goal = point_dist(self.coordinate, goal) <= self.radius

    ''' Check if robot whether reached or saw goal '''

    def check_goal(self, goal, true_sight):

        self.is_reach_goal(goal)
        if not self.reach_goal:
            self.is_saw_goal(goal, true_sight)

    ''' print status and information of robot '''

    def print_infomation(self):
        if self.no_way_to_goal:
            print("NO path to goal!")
        elif self.reach_goal:
            print("Reached goal!")
        elif self.saw_goal:
            print("Saw goal!")

        if print_traversalSights:
            print("traversal_sights:", self.traversal_sights)

        if print_visited_path:
            print("visited path:", self.visited_path)

    def finish(self):
        return self.no_way_to_goal or self.reach_goal

    ''' clear local information '''

    def clear_local(self):
        self.local_open_pts = []
        self.local_active_open_pts = []
        self.local_active_open_rank_pts = []

    ''' get local open points '''

    def get_local_open_points(self, open_sights):
        self.local_open_pts = []
        if len(open_sights) > 0:
            open_sights = np.array(open_sights)
            self.local_open_pts = open_sights[:, 2]  # local_openPts
            for i in range(len(self.local_open_pts)):
                self.local_open_pts[i][0] = approximately_num(self.local_open_pts[i][0])
                self.local_open_pts[i][1] = approximately_num(self.local_open_pts[i][1])
        return self.local_open_pts

    ''' check whether local open_points are active '''

    def get_local_active_open_points(self):

        # get local active point for local points
        self.local_active_open_pts = []
        if len(self.local_open_pts):  # new local found
            self.local_active_open_pts = self.local_open_pts

            # remove local_point which is inside explored area
            if len(self.traversal_sights) > 0:
                local_open_pts_status = [inside_global_true_sight(pt, self.vision_range, self.traversal_sights) for pt
                                         in self.local_active_open_pts]
                self.local_active_open_pts = self.local_active_open_pts[np.logical_not(local_open_pts_status)]

    def ranking_active_open_point(self, ranker, goal):
        ranks_new = []
        self.local_active_open_rank_pts = []
        # Ranking new active openPts then stack to global set.
        if len(self.local_active_open_pts) > 0:
            ranks_new = np.array([ranker.rank(self.coordinate, pt, goal) for pt in self.local_active_open_pts])

            # store local open points and its ranking 
            self.local_active_open_rank_pts = np.concatenate((self.local_active_open_pts, ranks_new), axis=1)
            pts = self.local_active_open_rank_pts[:, 0:2]
            pt_idx = 0
            # Look for existed (zero rewarded) points in reward table from local active open rank points
            for pt in pts:
                if tuple(pt) in self.reward_table:
                    if self.reward_table[tuple(pt)] == 0:
                        self.local_active_open_rank_pts[pt_idx, 2] = 0 # make it have rank zero
                pt_idx += 1

    ''' check whether local open_points are active '''

    def get_local_active_open_ranking_points(self, open_sights, ranker, goal):
        # get all local points from open sights
        self.get_local_open_points(open_sights)

        # get only active open point
        self.get_local_active_open_points()

        # ranking and store it to local active open ranking points
        self.ranking_active_open_point(ranker=ranker, goal=goal)

    ''' pick next point, where its ranking is highest, in given list '''

    def pick_next_point(self, open_points_list, goal):
        next_point = None
        next_pt_idx = -1
        reward = 0

        if self.saw_goal or self.reach_goal:
            next_point = goal
            reward = 1

        elif len(open_points_list) > 0:
            if self.f:
                ranks = open_points_list[:, 2]
                next_pt_idx = np.argmax(ranks)
                next_point = open_points_list[next_pt_idx, 0:2]

            incoming_dist = point_dist(self.coordinate, goal) - point_dist(next_point, goal)
            if incoming_dist < - self.vision_range / 2:
                # reward = -1 + -1 * round(abs(incoming_dist) / self.vision_range, 2)
                reward = -1 + -1 * round(point_dist(self.coordinate, next_point) / self.vision_range, 2)
            else:
                reward = -1

            print("vision range: ", self.vision_range)
            print("Distance travel to next point: ", point_dist(self.coordinate, next_point))
        # print('open points: ', open_points_list)
        return next_point, next_pt_idx, reward

    ''' remove active point form active list '''

    def remove_global_active_pts_by_index(self, point_idx):
        self.global_active_open_rank_pts = np.delete(self.global_active_open_rank_pts, point_idx, axis=0)

    ''' calcualte traveled path length '''

    def update_reward_table(self):
        idx = []
        # Find the point that has been punished
        for i, (key, value) in enumerate(self.final.items()):
            if value < -1.8:
                idx.append(i - (-value // 1))
        # Find the point that started the wrong way
        for i, (key, value) in enumerate(self.final.items()):
            if i in idx:
                self.final[key] = 0 # Reward it with zero value
        for key, value in self.final.items():
            if value == 0:
                print(key, value)

    def calculate_traveled_path_cost(self):
        cost = 0.0
        for path in self.visited_path:
            cost += path_cost(path)
        return cost

    ''' add local active and its ranking to global active points set '''

    def expand_global_open_ranking_points(self, local_active_open_pts):
        if len(local_active_open_pts) > 0:
            if len(self.global_active_open_rank_pts) == 0:
                self.global_active_open_rank_pts = np.array(local_active_open_pts)
            else:
                self.global_active_open_rank_pts = np.concatenate(
                    (self.global_active_open_rank_pts, local_active_open_pts), axis=0)
