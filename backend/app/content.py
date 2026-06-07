from __future__ import annotations

from typing import Any


SCENARIO_SEEDS: dict[str, dict[str, Any]] = {
    "li_quan_red_turban": {
        "id": "li_quan_red_turban",
        "title": "山东红袄：李全的扩张与归附",
        "era": "金末 宋金蒙角力时期",
        "summary": "你将扮演李全，在山东、淮海与南宋之间周旋，决定这支红袄军究竟是做乱世枭雄、地方军阀，还是借势而起的政治力量。",
        "player_role": "红袄军首领李全",
        "opening_situation": (
            "金廷压榨日重，山东流民与溃兵持续汇集。李全的旗号已经打响，"
            "但真正的问题不是能不能拉起队伍，而是这支队伍今后靠什么活、"
            "对谁借势、又要不要把自己交给更大的政权。"
        ),
        "historical_anchor": (
            "李全并不是单纯的流民军头领，他的处境始终夹在金、宋、蒙古与地方豪强之间。"
            "他的每一步都不只是打仗，更是结盟、投名、试探与反噬。"
        ),
        "primary_goal": "让李全与其部众在乱局中站稳脚跟，并为后续扩张争取最大主动权。",
        "failure_risk": (
            "若扩张过快、归附过深或内部控制失衡，这支队伍很快就会在围剿、离心和外部利用中被撕裂。"
        ),
        "initial_options": [
            {
                "id": "secure_grain_routes",
                "label": "先夺粮道，再稳人心",
                "brief": "优先控制粮仓、河渡与集市，把最基本的军粮和流民秩序抓在手里。",
                "strategic_hint": "偏向先固根基，再图声势。",
            },
            {
                "id": "approach_southern_song",
                "label": "先向南宋递话",
                "brief": "尝试借南宋名义与贸易通道，为自己争取合法性和外部空间。",
                "strategic_hint": "偏向借势保身，但会带来身份和忠诚问题。",
            },
            {
                "id": "swallow_local_militias",
                "label": "先吞并地方武装",
                "brief": "优先拉拢盐枭、寨主与团练，让李全迅速做大兵力规模。",
                "strategic_hint": "偏向抢速度，但内部整合风险极高。",
            },
        ],
        "opening_prompt_hint": "你可以先写李全是先抓粮、先借宋廷名分，还是先吞并周边武装。",
    },
    "zhang_juzheng_reform": {
        "id": "zhang_juzheng_reform",
        "title": "万历新政前夜：张居正的第一盘棋",
        "era": "明 万历初年",
        "summary": "你是张居正身边的核心政务参谋，要在幼主新立、内廷外朝相互牵制之际决定新政的第一落子。",
        "player_role": "张居正身边的核心政务参谋",
        "opening_situation": (
            "幼主新立，内阁、司礼监、言官和地方官都在试探彼此边界。国库吃紧、"
            "积弊深重，改革必须开始，但第一步落在哪里，将决定你接下来是推制度，"
            "还是先稳权力。"
        ),
        "historical_anchor": (
            "张居正的成功，并不只靠政策设计，更靠他在幼主时代对朝局节奏的精准掌控。"
        ),
        "primary_goal": "在不让朝局先行翻桌的前提下，为万历新政争取真正落地的起手优势。",
        "failure_risk": "若第一步过猛，改革会在全面结怨前就被定义成单纯的权势工程。",
        "initial_options": [
            {
                "id": "push_kaocheng",
                "label": "先推考成法",
                "brief": "抓考核、抓时限、抓执行，让中枢命令真正落到地方。",
                "strategic_hint": "执行见效最快，但最容易直接刺激官僚系统。",
            },
            {
                "id": "repair_finance",
                "label": "先动财政和田赋",
                "brief": "先摸清钱粮命脉，再谈其他改革。",
                "strategic_hint": "触及根本，但也最容易惊动既得利益。",
            },
            {
                "id": "stabilize_court_alliance",
                "label": "先稳住权力结构",
                "brief": "先处理内廷、外朝与言路关系，再推进制度。",
                "strategic_hint": "短期最稳，但容易被质疑只顾权术。",
            },
        ],
        "opening_prompt_hint": "你可以先抓执行、先抓钱粮，或先稳住朝局再谈制度推进。",
    },
    "yuan_shikai_korea": {
        "id": "yuan_shikai_korea",
        "title": "朝鲜风云：袁世凯与甲午前夜",
        "era": "清末 甲午战前的朝鲜",
        "summary": "你将扮演驻朝袁世凯，在清廷、朝鲜王室、日本势力与本地党争之间维持宗主影响力，并决定局势何时转向失控。",
        "player_role": "驻朝袁世凯",
        "opening_situation": (
            "朝鲜宫廷内斗不断，亲清、亲日与本地势力彼此倾轧。清廷希望维持宗主地位，"
            "却又不愿无限加码；日本则在贸易、军事与政治影响上步步紧逼。袁世凯必须在"
            "有限授权下控制局面，但每一次过强或过弱的动作，都可能让局势提前破裂。"
        ),
        "historical_anchor": (
            "袁世凯在朝鲜的角色并不只是外交官，更像一个代表清廷意志、操盘朝鲜局势、"
            "同时又受制于清廷内部犹疑的前线政治执行者。"
        ),
        "primary_goal": "在不提前引爆中日正面摊牌的前提下，维持清廷在朝鲜的实际影响力。",
        "failure_risk": (
            "若对朝鲜王室压得太重、对日本试探判断失误，或对清廷汇报节奏拿捏不准，"
            "局势会迅速滑向全面外交和军事失控。"
        ),
        "initial_options": [
            {
                "id": "stabilize_korean_court",
                "label": "先稳住朝鲜宫廷",
                "brief": "优先协调王室与关键派系，压住内斗，避免宫廷先乱成突破口。",
                "strategic_hint": "偏向宫廷操盘，但会拖慢对外布局。",
            },
            {
                "id": "signal_strength_to_japan",
                "label": "先向日方释放强硬信号",
                "brief": "通过驻军、训政或外交姿态表明清廷不会轻易让出朝鲜主导权。",
                "strategic_hint": "短期能立威，但误判后果极大。",
            },
            {
                "id": "memorial_to_qing_court",
                "label": "先向清廷争取更大授权",
                "brief": "尽快向中枢上奏，请求更清晰的政策边界、资源与指挥空间。",
                "strategic_hint": "能增强合法性，但也会暴露你对局势的焦虑程度。",
            },
        ],
        "opening_prompt_hint": "你可以先写袁世凯是先控宫廷、先压日本，还是先回头向清廷争取授权。",
    },
}


def list_scenarios() -> list[dict[str, str]]:
    return [
        {
            "id": scenario["id"],
            "title": scenario["title"],
            "era": scenario["era"],
            "summary": scenario["summary"],
        }
        for scenario in SCENARIO_SEEDS.values()
    ]


def get_scenario_seed(scenario_id: str) -> dict[str, Any]:
    scenario = SCENARIO_SEEDS.get(scenario_id)
    if scenario is None:
        raise KeyError(scenario_id)
    return scenario
