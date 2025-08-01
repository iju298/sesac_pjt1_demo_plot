import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def save_fig_to_html(fig, output_path: str):
    """
    Plotly figure 객체를 HTML 파일로 저장합니다.

    Parameters:
    - fig: Plotly 그래프 객체
    - output_path (str): 저장할 HTML 파일 경로
    """
    if fig is None:
        print("⚠️ 저장할 fig 객체가 없습니다.")
        return
    fig.write_html(output_path)
    print(f"✅ 그래프가 HTML로 저장되었습니다: {output_path}")


def plot_student_lecture_time(student_df: pd.DataFrame, student_name: str, lecture: int, save:bool= True, path='./plots'):

    # 데이터 필터링
    df = student_df[(student_df["student_name"] == student_name) & (student_df["lecture"] == lecture)]

    # 데이터 유무 확인
    if df.empty:
        print(f"No data found for student '{student_name}' in Lecture {lecture}.")
        return

    # datetime 변환
    df["last_study_datetime"] = pd.to_datetime(df["last_study_datetime"])

    # 라인 플롯 생성
    fig = px.line(
        df,
        x="chapter",
        y="time",
        markers=True,
        hover_data={"last_study_datetime": True},
        labels={"time": "Study Time (min)", "chapter": "Chapter"},
        title=f"{student_name}'s Study Time per Chapter (Lecture {lecture})"
    )

    # 라인 스타일 및 축 설정
    fig.update_traces(line=dict(width=7))  # 라인 두께 조정

    fig.update_layout(
    xaxis=dict(
            dtick=1,
            tickfont=dict(size=22),  # x축 눈금 폰트
            title=dict(font=dict(size=24))  # ✅ x축 타이틀 폰트
        ),
        yaxis=dict(
            range=[0, df["time"].max() * 1.1],
            tickfont=dict(size=22),  # y축 눈금 폰트
            title=dict(font=dict(size=24))  # ✅ y축 타이틀 폰트
        ),
        title=dict(font=dict(size=20))  # 전체 그래프 제목
    )



    if save:
        save_fig_to_html(fig, output_path=f'{path}/{student_name}_lec_{lecture}_time.html')

    return fig



def plot_student_chapter_count(student_df: pd.DataFrame, student_name: str, lecture: int, save:bool= True, path='./plots'):
    """
    특정 학생의 특정 강의에서 챕터별 틀린 횟수(count)를 선형 그래프로 시각화하고,
    hover 시 마지막 수강 일시를 표시합니다.
    
    Parameters:
    - student_df (pd.DataFrame): 수강 데이터
    - student_name (str): 학생 이름
    - lecture (int): 강의 번호
    """
    # 필터링
    df = student_df[(student_df["student_name"] == student_name) & (student_df["lecture"] == lecture)]

    if df.empty:
        print(f"No data found for student '{student_name}' in Lecture {lecture}.")
        return

    df["last_study_datetime"] = pd.to_datetime(df["last_study_datetime"])

    # 라인 플롯
    fig = px.line(
        df,
        x="chapter",
        y="count",
        markers=True,
        hover_data={"last_study_datetime": True},
        labels={"chapter": "Chapter", "count": "Incorrect Count"},
        title=f"{student_name}'s Incorrect Count per Chapter (Lecture {lecture})"
    )

    fig.update_traces(line=dict(width=7))  # 라인 두께 조정

    fig.update_layout(
        xaxis=dict(
            dtick=1,
            tickfont=dict(size=22),  # X축 눈금 폰트
            title=dict(font=dict(size=24))  # X축 제목 폰트
        ),
        yaxis=dict(
            range=[0, df["count"].max() * 1.1],
            tickfont=dict(size=22),  # Y축 눈금 폰트
            title=dict(font=dict(size=24))  # Y축 제목 폰트
        ),
        title=dict(font=dict(size=20))  # 전체 그래프 제목 폰트
    )


    if save:
        save_fig_to_html(fig, output_path=f'{path}/{student_name}_lec_{lecture}_incorrect_count.html')

    return fig


def plot_student_proficiency_radar(student_df: pd.DataFrame, lecture_df: pd.DataFrame, student_name: str, save:bool= True, path='./plots'):
    """
    한 학생의 시험 점수와 강의 특성별 weight를 기반으로 숙련도를 계산하고,
    skill별 최대 이론값으로 정규화하여 0~100 점수로 레이더 차트를 시각화합니다.

    Parameters:
    - student_df (pd.DataFrame): 학생 시험 및 수강 데이터
    - lecture_df (pd.DataFrame): 강의별 특성 가중치 (Dart, Widget 등 포함)
    - student_name (str): 조회할 학생 이름
    """
    # 1. 해당 학생 데이터 필터링
    stu_df = student_df[student_df["student_name"] == student_name]
    if stu_df.empty:
        print(f"No data found for student '{student_name}'")
        return

    # 2. 시험 평균 계산
    stu_df["exam_avg"] = (stu_df["exam1"] + stu_df["exam2"]) / 2

    # 3. 강의 특성 melt
    melted_lecture = lecture_df.melt(id_vars=["lecture", "chapter"],
                                     var_name="skill", value_name="weight")

    # 4. join & weighted score 계산
    merged = pd.merge(stu_df[["lecture", "chapter", "exam_avg"]],
                      melted_lecture,
                      on=["lecture", "chapter"],
                      how="inner")
    merged["weighted_score"] = merged["exam_avg"] * merged["weight"]

    # 5. skill별 학생 점수 및 max score 계산
    skill_score = merged.groupby("skill")["weighted_score"].sum().reset_index(name="raw_score")
    skill_max = melted_lecture.groupby("skill")["weight"].sum().reset_index(name="weight_sum")
    skill_max["max_score"] = skill_max["weight_sum"] * 100  # 시험 만점 기준

    # 6. 정규화: 0~100점으로 변환
    result = pd.merge(skill_score, skill_max, on="skill")
    result["normalized_score"] = (result["raw_score"] / result["max_score"]) * 100

    # 정렬 (선택)
    result = result.sort_values("skill")

    # 7. 레이더 차트
    categories = result["skill"].tolist()
    values = result["normalized_score"].tolist()
    values += values[:1]  # 도형 닫기용

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
    r=values,
    theta=categories + [categories[0]],
    fill='toself',
    name=student_name,
    text=[f"{v:.1f}" for v in values],
    textposition="top center",
    mode='lines+markers+text',
    textfont=dict(size=16)  # 숫자 크기 조절 (기본보다 크게)
    ))


    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=True,
        title=f"{student_name}'s Skill Proficiency"
    )

    fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100]),
        angularaxis=dict(
            tickfont=dict(size=20),
            rotation=90,
            direction='clockwise'
        )
    ),
    showlegend=True,
    title=dict(text=f"{student_name}'s Skill Proficiency", font=dict(size=20))
)


    if save:
        save_fig_to_html(fig, output_path=f'{path}/{student_name}_skill.html')

    return fig


def report_student_skill_analysis(student_df: pd.DataFrame, lecture_df: pd.DataFrame, student_name: str):
    """
    주어진 학생의 시험 점수와 강의 특성 weight를 기반으로
    최고/최저 숙련도 기술, 해당 skill의 대표 챕터, 전체 진척도를 분석합니다.

    Parameters:
    - student_df (pd.DataFrame): 학생 시험 데이터
    - lecture_df (pd.DataFrame): 강의-챕터별 skill weight 데이터
    - student_name (str): 분석할 학생 이름

    Returns:
    - dict: {
        best_skill: {'skill': str, 'normalized_score': float},
        worst_skill: {'skill': str, 'normalized_score': float},
        most_weighted_chapter_for_worst_skill: {'lecture': int, 'chapter': int, 'weight': float},
        progress_percent: float
      }
    """
    # 해당 학생 데이터 필터링
    stu_df = student_df[student_df["student_name"] == student_name]
    if stu_df.empty:
        return f"No data found for student '{student_name}'"

    stu_df = stu_df.copy()
    stu_df["exam_avg"] = (stu_df["exam1"] + stu_df["exam2"]) / 2

    # 진척도 계산 (전체 lecture-chapter 수 대비 현재 수강 챕터의 누적 progress)
    total_chapters = lecture_df.shape[0]
    total_progress = stu_df["progress"].sum()
    progress_percent = (total_progress / total_chapters) * 100

    # skill별 가중 점수 계산
    melted_lecture = lecture_df.melt(id_vars=["lecture", "chapter"],
                                     var_name="skill", value_name="weight")
    merged = pd.merge(stu_df[["lecture", "chapter", "exam_avg"]],
                      melted_lecture,
                      on=["lecture", "chapter"],
                      how="inner")
    merged["weighted_score"] = merged["exam_avg"] * merged["weight"]

    # skill별 점수 집계 및 정규화
    skill_score = merged.groupby("skill")["weighted_score"].sum().reset_index(name="raw_score")
    skill_max = melted_lecture.groupby("skill")["weight"].sum().reset_index(name="weight_sum")
    skill_max["max_score"] = skill_max["weight_sum"] * 100

    result = pd.merge(skill_score, skill_max, on="skill")
    result["normalized_score"] = (result["raw_score"] / result["max_score"]) * 100

    # 최고/최저 skill 찾기
    best_skill_row = result.loc[result["normalized_score"].idxmax()]
    worst_skill_row = result.loc[result["normalized_score"].idxmin()]
    worst_skill = worst_skill_row["skill"]

    # 해당 skill의 가장 높은 weight를 가진 챕터
    best_chapter = lecture_df.loc[lecture_df[worst_skill].idxmax()]
    best_chapter_info = {
        "lecture": int(best_chapter["lecture"]),
        "chapter": int(best_chapter["chapter"]),
        "weight": best_chapter[worst_skill]
    }

    return {
        "best_skill": best_skill_row[["skill", "normalized_score"]].to_dict(),
        "worst_skill": worst_skill_row[["skill", "normalized_score"]].to_dict(),
        "most_weighted_chapter_for_worst_skill": best_chapter_info,
        "progress_percent": round(progress_percent, 2)
    }



def plot_score_distribution_by_chapter(student_df: pd.DataFrame, lecture: int, chapter: int,
                                       exam='all', bin_size: int = 10, save:bool= True, path='./plots'):
    """
    특정 lecture-chapter에 대해 시험 점수 구간별 학생 수를 바 차트로 시각화합니다.

    Parameters:
    - student_df: 수강 데이터프레임
    - lecture: 강의 번호
    - chapter: 챕터 번호
    - exam: 'all', 1, 2 중 하나 (기본 'all' → exam1과 exam2의 평균)
    - bin_size: 점수 구간 폭 (기본 10)

    Returns:
    - Plotly bar chart 출력
    """
    # 데이터 필터링
    df = student_df[(student_df["lecture"] == lecture) & (student_df["chapter"] == chapter)]
    if df.empty:
        print(f"No student data found for Lecture {lecture}, Chapter {chapter}")
        return

    df = df.copy()

    # 선택한 시험 점수 계산
    if exam == "all":
        df["score"] = (df["exam1"] + df["exam2"]) / 2
        exam_label = "Average of Exam1 & Exam2"
        exam_info = 'exam_all'
    elif isinstance(exam, int) and exam in [1, 2]:
        df["score"] = df[f"exam{exam}"]
        exam_label = f"Exam{exam} Score"
        exam_info = f'exam_{exam}'
    else:
        raise ValueError("exam 파라미터는 'all' 또는 정수 1, 2 중 하나여야 합니다.")

    # 점수 구간 분류
    df["score_bin"] = pd.cut(df["score"],
                             bins=range(0, 101, bin_size),
                             right=False,
                             include_lowest=True)

    # 구간별 count
    score_dist = df["score_bin"].value_counts().sort_index().reset_index()
    score_dist.columns = ["Score Range", "Student Count"]
    score_dist["Score Range"] = score_dist["Score Range"].astype(str)

    # 시각화
    fig = px.bar(score_dist,
                 x="Score Range",
                 y="Student Count",
                 title=f"Score Distribution (Lecture {lecture}, Chapter {chapter}) - {exam_label}",
                 labels={"Score Range": "Score Interval", "Student Count": "Number of Students"})

    fig.update_layout(xaxis_type="category")
    
    if save:
        save_fig_to_html(fig, output_path=f'{path}/lec_{lecture}_ch_{chapter}_{exam_info}_score.html')


import plotly.express as px
import pandas as pd

def plot_chapter_avg_time_pie(student_df: pd.DataFrame, lecture: int, save: bool = True, path='./plots'):
    """
    특정 lecture에서 chapter별 평균 학습 소요시간의 비중을 파이차트로 시각화합니다.
    챕터 번호 순서로 정렬하며, 텍스트는 차트 내부에 가로로 표시되고 단위 (m)를 포함합니다.
    """
    # 1. 강의 필터링
    df = student_df[student_df["lecture"] == lecture]
    if df.empty:
        print(f"No data found for Lecture {lecture}")
        return

    # 2. chapter별 평균 학습시간 계산 후 정렬
    chapter_avg = df.groupby("chapter")["time"].mean().reset_index()
    chapter_avg = chapter_avg.sort_values("chapter")

    # 3. 파이차트 생성 (순서 고정)
    fig = px.pie(
        chapter_avg,
        names="chapter",
        values="time",
        title=f"Avg Study Time by Chapter - Lecture {lecture}",
        hole=0.4,
        category_orders={"chapter": chapter_avg["chapter"].tolist()}
    )

    # 4. 텍스트 설정: 내부, 가로, (m) 단위 표시
    fig.update_traces(
        textinfo='none',
        texttemplate='%{label}<br>%{percent}<br>%{value:.1f}(min)',
        textposition="inside",
        insidetextorientation="horizontal",
        textfont_size=25
    )

    fig.update_layout(title=dict(font=dict(size=20)))

    # 5. 저장
    if save:
        save_fig_to_html(fig, output_path=f'{path}/lec_{lecture}_chapter_avg_time_pie.html')

    return fig



def plot_chapter_exam_score(student_df: pd.DataFrame, lecture: int, save: bool = True, path='./plots'):
    """
    특정 lecture에 대해 챕터별 시험 평균 점수를 라인 플롯으로 시각화합니다.

    Parameters:
    - student_df (pd.DataFrame): 수강 데이터
    - lecture (int): 강의 번호
    - save (bool): 저장 여부
    - path (str): 저장 경로

    Returns:
    - plotly.graph_objects.Figure
    """
    # 1. 강의 필터링
    df = student_df[student_df["lecture"] == lecture]
    if df.empty:
        print(f"No data found for Lecture {lecture}")
        return

    # 2. 평균 시험 점수 계산
    df = df.copy()
    df["exam_avg"] = (df["exam1"] + df["exam2"]) / 2

    # 3. 챕터별 평균 점수 집계
    chapter_avg = df.groupby("chapter")["exam_avg"].mean().reset_index()
    chapter_avg = chapter_avg.sort_values("chapter")

    # 4. 라인 플롯 생성
    fig = px.line(
        chapter_avg,
        x="chapter",
        y="exam_avg",
        markers=True,
        labels={"chapter": "Chapter", "exam_avg": "Average Exam Score"},
        title=f"Avg Exam Score by Chapter - Lecture {lecture}"
    )

    fig.update_traces(line=dict(width=7))
    fig.update_layout(
        xaxis=dict(dtick=1, tickfont=dict(size=22), title=dict(font=dict(size=24))),
        yaxis=dict(range=[0, 100], tickfont=dict(size=22), title=dict(font=dict(size=24))),
        title=dict(font=dict(size=20))
    )

    if save:
        save_fig_to_html(fig, output_path=f'{path}/lec_{lecture}_chapter_exam_avg_line.html')

    return fig



def plot_chapter_progress_bar(student_df: pd.DataFrame, lecture: int, save: bool = True, path='./plots'):
    """
    특정 lecture에 대해 챕터별 평균 진척도(progress)를 바 차트로 시각화합니다.

    Parameters:
    - student_df (pd.DataFrame): 수강 데이터
    - lecture (int): 강의 번호
    - save (bool): 저장 여부
    - path (str): 저장 경로

    Returns:
    - plotly.graph_objects.Figure
    """
    # 1. 필터링
    df = student_df[student_df["lecture"] == lecture]
    if df.empty:
        print(f"No data found for Lecture {lecture}")
        return

    # 2. chapter별 평균 progress 계산
    chapter_progress = df.groupby("chapter")["progress"].mean().reset_index()
    chapter_progress = chapter_progress.sort_values("chapter")
    chapter_progress['progress']*=100
    # 3. 바 차트 생성
    fig = px.bar(
        chapter_progress,
        x="chapter",
        y="progress",
        labels={"chapter": "Chapter", "progress": "Avg Progress (%)"},
        title=f"Average Progress per Chapter - Lecture {lecture}",
        text_auto=".1f"
    )

    # 4. 스타일 조정
    fig.update_layout(
        yaxis=dict(range=[0, 100], tickfont=dict(size=22), title=dict(font=dict(size=24))),
        xaxis=dict(dtick=1, tickfont=dict(size=22), title=dict(font=dict(size=24))),
        title=dict(font=dict(size=20))
    )
    fig.update_traces(textfont_size=20)  # ✅ 바 위 숫자 크기 조절

    if save:
        save_fig_to_html(fig, output_path=f'{path}/lec_{lecture}_chapter_progress_bar.html')

    return fig
