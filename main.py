import random
import matplotlib.pyplot as plt
import numpy as np

# 配置全局参数（可调整战术/概率）
class PingPongConfig:
    # 选手基础参数：[前三板得分率, 相持得分率, 关键分抗压系数(>1增强), 发球优势率]
    PLAYER_A = {"name": "马龙", "serve_3": 0.75, "rally": 0.6, "key_point": 1.2, "serve_adv": 0.6}
    PLAYER_B = {"name": "伊藤美诚", "serve_3": 0.7, "rally": 0.55, "key_point": 1.1, "serve_adv": 0.58}
    WIN_SCORE = 11  # 单局获胜分数
    DEUCE_DIFF = 2  # 平分后需领先2分获胜
    SIM_TIMES = 1000  # 模拟比赛次数

# 单回合得分模拟（核心：区分前三板/相持、关键分）
def simulate_round(server, receiver, is_key_point=False):
    """
    模拟单个回合得分
    :param server: 发球方（字典）
    :param receiver: 接发球方（字典）
    :param is_key_point: 是否关键分（10平后/赛点）
    :return: 得分方（字典）
    """
    # 1. 判定是否进入前三板（乒乓球前三板得分占比约60%）
    is_3_board = random.random() < 0.6
    
    if is_3_board:
        # 前三板：发球方优势 + 关键分修正
        server_win_prob = server["serve_3"] * server["serve_adv"]
        if is_key_point:
            server_win_prob *= server["key_point"]
            # 接发球方关键分抗压（反向修正）
            receiver_win_prob = (1 - server_win_prob) * receiver["key_point"]
            server_win_prob = 1 - receiver_win_prob
        if random.random() < server_win_prob:
            return server
        else:
            return receiver
    else:
        # 相持阶段：基础得分率 + 关键分修正
        server_win_prob = server["rally"]
        if is_key_point:
            server_win_prob *= server["key_point"]
        if random.random() < server_win_prob:
            return server
        else:
            return receiver

# 单局比赛模拟
def simulate_game(player1, player2):
    score1, score2 = 0, 0
    # 发球轮换（每2分换发球，11分制规则）
    server = player1 if random.choice([True, False]) else player2
    serve_count = 0
    
    while True:
        # 判定是否关键分（10平后）
        is_key_point = (score1 >= 10 and score2 >= 10) or \
                       (score1 == PingPongConfig.WIN_SCORE - 1) or (score2 == PingPongConfig.WIN_SCORE - 1)
        
        # 模拟回合得分
        winner = simulate_round(server, player1 if server == player2 else player2, is_key_point)
        
        # 更新分数
        if winner == player1:
            score1 += 1
        else:
            score2 += 1
        
        # 发球轮换
        serve_count += 1
        if serve_count >= 2:
            server = player1 if server == player2 else player2
            serve_count = 0
        
        # 判定单局胜负
        if (score1 >= PingPongConfig.WIN_SCORE or score2 >= PingPongConfig.WIN_SCORE):
            if abs(score1 - score2) >= PingPongConfig.DEUCE_DIFF:
                return {"winner": player1 if score1 > score2 else player2,
                        "score": (score1, score2),
                        "key_point_rounds": 1 if is_key_point else 0}

# 多局比赛模拟（五局三胜）
def simulate_match(player1, player2, best_of=5):
    player1_wins = 0
    player2_wins = 0
    game_details = []
    total_key_point_rounds = 0  # 累计关键分回合数
    
    while player1_wins < (best_of + 1) // 2 and player2_wins < (best_of + 1) // 2:
        game_result = simulate_game(player1, player2)
        game_details.append(game_result)
        total_key_point_rounds += game_result["key_point_rounds"]
        
        if game_result["winner"] == player1:
            player1_wins += 1
        else:
            player2_wins += 1
    
    return {"match_winner": player1 if player1_wins > player2_wins else player2,
            "game_details": game_details,
            "total_key_point_rounds": total_key_point_rounds}

# 批量模拟+统计分析
def batch_simulation(player1, player2, sim_times=PingPongConfig.SIM_TIMES):
    # 统计指标
    player1_match_wins = 0
    player2_match_wins = 0
    total_key_point_rounds = 0
    score_diff_dist = []  # 单局分差分布
    key_point_win_rate = {"A": 0, "B": 0}  # 关键分胜率
    key_point_total = {"A": 0, "B": 0}
    
    for _ in range(sim_times):
        match_result = simulate_match(player1, player2)
        total_key_point_rounds += match_result["total_key_point_rounds"]
        
        # 统计比赛胜负
        if match_result["match_winner"] == player1:
            player1_match_wins += 1
        else:
            player2_match_wins += 1
        
        # 统计单局分差、关键分
        for game in match_result["game_details"]:
            score1, score2 = game["score"]
            score_diff_dist.append(abs(score1 - score2))
            
            # 关键分胜负统计
            if game["key_point_rounds"] == 1:
                if game["winner"] == player1:
                    key_point_win_rate["A"] += 1
                    key_point_total["A"] += 1
                    key_point_total["B"] += 1
                else:
                    key_point_win_rate["B"] += 1
                    key_point_total["A"] += 1
                    key_point_total["B"] += 1
    
    # 计算胜率
    player1_rate = player1_match_wins / sim_times
    player2_rate = player2_match_wins / sim_times
    # 关键分胜率（避免除零）
    key_a_rate = key_point_win_rate["A"] / key_point_total["A"] if key_point_total["A"] > 0 else 0
    key_b_rate = key_point_win_rate["B"] / key_point_total["B"] if key_point_total["B"] > 0 else 0
    
    return {
        "player1_win_rate": player1_rate,
        "player2_win_rate": player2_rate,
        "avg_score_diff": np.mean(score_diff_dist),
        "key_point_win_rate": {"A": key_a_rate, "B": key_b_rate},
        "total_key_point_rounds": total_key_point_rounds / sim_times  # 场均关键分回合数
    }

# 可视化结果
def plot_results(stats, player1_name, player2_name):
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    
    # 1. 比赛胜率对比
    ax1.bar([player1_name, player2_name], [stats["player1_win_rate"], stats["player2_win_rate"]], color=["red", "blue"])
    ax1.set_title("比赛胜率（{}次模拟）".format(PingPongConfig.SIM_TIMES))
    ax1.set_ylabel("胜率")
    ax1.set_ylim(0, 1)
    
    # 2. 关键分胜率对比
    ax2.bar([f"{player1_name}(关键分)", f"{player2_name}(关键分)"], 
            [stats["key_point_win_rate"]["A"], stats["key_point_win_rate"]["B"]], 
            color=["darkred", "darkblue"])
    ax2.set_title("关键分胜率")
    ax2.set_ylabel("胜率")
    ax2.set_ylim(0, 1)
    
    # 3. 场均关键分回合数
    ax3.bar(["场均关键分回合数"], [stats["total_key_point_rounds"]], color="green")
    ax3.set_title("场均关键分回合数")
    ax3.set_ylabel("次数")
    
    # 4. 单局平均分差
    ax4.bar(["单局平均分差"], [stats["avg_score_diff"]], color="orange")
    ax4.set_title("单局平均分差")
    ax4.set_ylabel("分差")
    
    plt.tight_layout()
    plt.show()

# 主执行逻辑
if __name__ == "__main__":
    # 加载选手配置
    player_a = PingPongConfig.PLAYER_A
    player_b = PingPongConfig.PLAYER_B
    
    # 批量模拟
    simulation_stats = batch_simulation(player_a, player_b)
    
    # 打印统计结果
    print("="*50)
    print(f"模拟{PingPongConfig.SIM_TIMES}场五局三胜比赛结果：")
    print(f"{player_a['name']} 总胜率：{simulation_stats['player1_win_rate']:.2%}")
    print(f"{player_b['name']} 总胜率：{simulation_stats['player2_win_rate']:.2%}")
    print(f"单局平均分差：{simulation_stats['avg_score_diff']:.2f} 分")
    print(f"{player_a['name']} 关键分胜率：{simulation_stats['key_point_win_rate']['A']:.2%}")
    print(f"{player_b['name']} 关键分胜率：{simulation_stats['key_point_win_rate']['B']:.2%}")
    print(f"场均关键分回合数：{simulation_stats['total_key_point_rounds']:.2f}")
    print("="*50)
    
    # 可视化
    plot_results(simulation_stats, player_a["name"], player_b["name"])
