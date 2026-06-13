// dummy.c - 修炼傀儡（训练加速器）
// 与它对练时，每心跳按玩家当前经验成比例发放经验与潜能：
//   exp_gain = max(2, combat_exp/500)   → 指数曲线，τ≈500s
//   pot_gain = max(1, combat_exp/2000)
// 战斗属性设计：出手极快(cor 200)、必中(apply/attack 60)、零伤害(str 1/damage 0)、
// 打不死(kee 100万/armor 1万) —— 理想陪练，战斗通道判定照常触发。

inherit NPC;

void create()
{
	set_name("修炼傀儡", ({ "training dummy", "dummy" }) );
	set("long",
		"一具以精铁打造的修炼傀儡，关节处镶著奇异的灵石，\n"
		"浑身散发著淡淡的灵气。与它对练似乎能急速增进实战经验。\n");
	set("gender", "无性");
	set("age", 1000);

	set("str", 1);
	set("con", 100);
	set("cor", 200);
	set("cps", 1);
	set("int", 1);

	set("max_gin", 1000000);
	set("max_kee", 1000000);
	set("max_sen", 1000000);

	set("combat_exp", 100);
	set_temp("apply/attack", 60);
	set_temp("apply/damage", 0);
	set_temp("apply/dodge", 40);
	set_temp("apply/armor", 10000);

	set("attitude", "heroism");
	setup();
}

void heart_beat()
{
	object *obs;
	object ob;
	int i, exp, gain, pot;

	::heart_beat();

	if( !environment() ) return;
	obs = all_inventory(environment());
	for(i=0; i<sizeof(obs); i++) {
		ob = obs[i];
		if( !userp(ob) || !living(ob) ) continue;
		if( !ob->is_fighting(this_object()) ) continue;
		exp = (int)ob->query("combat_exp");
		gain = exp / 500;
		if( gain < 2 ) gain = 2;
		ob->add("combat_exp", gain);
		pot = exp / 2000;
		if( pot < 1 ) pot = 1;
		ob->add("potential", pot);
	}
}
