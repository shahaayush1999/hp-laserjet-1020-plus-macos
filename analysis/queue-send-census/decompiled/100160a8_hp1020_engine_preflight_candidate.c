/* Function: 100160a8 hp1020_engine_preflight_candidate */


/* medium confidence: Engine preflight/status refresh path */

void hp1020_engine_preflight_candidate(void)

{
  uint uVar1;
  undefined *puVar2;
  uint *puVar3;
  undefined *puVar4;
  undefined1 uVar5;
  int iVar6;
  undefined4 local_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  undefined4 uStack_28;
  undefined4 uStack_24;

  local_40 = 0x17;
  uStack_38 = 0;
  uStack_34 = 0;
  uStack_3c = DAT_100063dc;
  hp1020_queue_send_candidate(1,&local_40);
  puVar3 = hp1020_engine_command_reg_table_word;
  uVar1 = DAT_10005e74;
  iVar6 = 0;
  memw();
  memw();
  *hp1020_engine_command_reg_table_word = *hp1020_engine_command_reg_table_word | DAT_10005e74;
  memw();
  uVar1 = *puVar3 & uVar1;
  while( true ) {
    if (uVar1 == 0) {
      threadx_sleep_candidate(0x3c);
      puVar4 = PTR_DAT_10006998;
      puVar2 = PTR_DAT_10006920;
      *(undefined **)(PTR_DAT_10006920 + 0x48) = PTR_DAT_10006994;
      *(undefined **)(puVar2 + 0x4c) = puVar4;
      *(undefined4 *)(puVar2 + 0x54) = 0;
      puVar2[0x58] = 0xff;
      uVar5 = hp1020_datastore_get_value_candidate(0xf);
      hp1020_engine_event_0x0f_config_callback_candidate(0xf,uVar5);
      FUN_10015d14();
      return;
    }
    threadx_sleep_candidate(0x14);
    iVar6 = iVar6 + 1;
    if ((*(int *)(PTR_DAT_10006920 + 0x24) != 0) || (iVar6 == 0x1e)) break;
    memw();
    uVar1 = *hp1020_engine_command_reg_table_word & DAT_10005e74;
  }
  uStack_30 = 0x17;
  uStack_28 = 0;
  uStack_24 = 0;
  uStack_2c = DAT_1000692c;
  hp1020_queue_send_candidate(1,&uStack_30);
  return;
}
