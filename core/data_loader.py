import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .constants import (
    DANCE_TYPES,
    MOVEMENT_TYPES,
    LEVELS,
    TEACHERS,
    COMPETITION_STAGES,
    HR_ZONES,
    HR_ZONE_BASE_VALUES,
    LEVEL_BASE_SCORES,
)
from .cycles import add_cycle_column


def generate_sample_data(n=600):
    np.random.seed(42)
    start_date = datetime(2025, 9, 1)
    records = []
    for i in range(n):
        date = start_date + timedelta(days=int(i * 90 / n))
        dance = np.random.choice(DANCE_TYPES)
        movement = np.random.choice(MOVEMENT_TYPES)
        level = np.random.choice(LEVELS, p=[0.25, 0.35, 0.25, 0.15])
        teacher = np.random.choice(TEACHERS)
        stage = np.random.choice(COMPETITION_STAGES, p=[0.4, 0.25, 0.2, 0.15])
        duration = np.random.randint(30, 150)
        hr_zone = np.random.choice(HR_ZONES, p=[0.15, 0.3, 0.25, 0.2, 0.1])
        avg_hr = HR_ZONE_BASE_VALUES
        heart_rate = avg_hr[hr_zone] + np.random.randint(-8, 9)
        base_fatigue = np.random.randint(2, 8)
        duration_factor = (duration - 60) / 120
        hr_factor = (heart_rate - 100) / 100
        fatigue = np.clip(base_fatigue + duration_factor * 2 + hr_factor * 1.5, 1, 10)
        fatigue = round(fatigue, 1)

        base_soft = LEVEL_BASE_SCORES["软开度"][level]
        base_rot = LEVEL_BASE_SCORES["旋转稳定度"][level]
        base_jump = LEVEL_BASE_SCORES["跳跃高度"][level]
        base_comp = LEVEL_BASE_SCORES["动作完成度"][level]

        fatigue_penalty = fatigue * 1.2
        duration_penalty = max(0, (duration - 90) * 0.15)
        hr_bonus = (heart_rate - 100) * 0.05 if heart_rate > 120 else 0

        soft = np.clip(base_soft - fatigue_penalty * 0.5 + hr_bonus + np.random.normal(0, 5), 0, 100)
        rot = np.clip(base_rot - fatigue_penalty * 0.8 + hr_bonus * 0.5 + np.random.normal(0, 6), 0, 100)
        jump = np.clip(base_jump - fatigue_penalty * 0.6 + np.random.normal(0, 5), 0, 100)
        comp = np.clip(base_comp - fatigue_penalty * 0.7 - duration_penalty + np.random.normal(0, 5), 0, 100)

        if dance == "身韵":
            comp += 3
        if movement == "软开度":
            soft += 5
        if movement == "旋转":
            rot += 5
        if movement == "跳跃":
            jump += 5

        if stage == "赛前集训":
            duration = int(duration * 1.3)
            fatigue = min(10, fatigue * 1.2)
        if stage == "比赛周":
            comp += 5
            fatigue = min(10, fatigue * 1.1)

        records.append({
            "日期": date.strftime("%Y-%m-%d"),
            "舞种": dance,
            "动作类型": movement,
            "学员级别": level,
            "指导老师": teacher,
            "比赛阶段": stage,
            "训练时长_分钟": duration,
            "心率区间": hr_zone,
            "平均心率": heart_rate,
            "主观疲劳评分": round(fatigue, 1),
            "软开度": round(soft, 1),
            "旋转稳定度": round(rot, 1),
            "跳跃高度": round(jump, 1),
            "动作完成度": round(comp, 1),
        })
    return pd.DataFrame(records)


def load_data(uploaded, use_sample):
    if uploaded is not None:
        df = pd.read_csv(uploaded)
    elif use_sample:
        df = generate_sample_data()
    else:
        return None
    df = add_cycle_column(df)
    return df
