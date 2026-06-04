/* Function: 100139e4 hp1020_control_panel_thread_candidate */


/* data-store subscriber mapping candidate */

void hp1020_control_panel_thread_candidate(void)

{
  byte bVar1;
  bool bVar2;
  uint *puVar3;
  undefined *puVar4;
  uint uVar5;
  uint uVar6;

  uVar5 = FUN_10012020();
  puVar4 = hp1020_control_panel_datastore_callback_ptr_word;
  hp1020_datastore_register_callback_subscriber_candidate
            (0x18,hp1020_control_panel_datastore_callback_ptr_word);
  hp1020_datastore_register_callback_subscriber_candidate(0x19,puVar4);
  threadx_sleep_candidate(4);
  puVar3 = DAT_10006740;
  memw();
  memw();
  *DAT_1000673c = *DAT_1000673c | (uint)PTR_LAB_10006374;
  memw();
  memw();
  *puVar3 = *puVar3 | DAT_10005f60;
  FUN_1001215c(1);
  FUN_10012184(1);
  puVar3 = DAT_100064cc;
  bVar2 = false;
  do {
    bVar1 = *PTR_DAT_10006728;
    if (bVar1 == 1) {
      memw();
      uVar6 = *puVar3 & DAT_100066c4;
LAB_10013a91:
      memw();
      *puVar3 = uVar6;
    }
    else if (bVar1 < 2) {
      if (bVar1 == 0) {
LAB_10013a85:
        memw();
        uVar6 = *puVar3 | DAT_100066a0;
        goto LAB_10013a91;
      }
    }
    else if (bVar1 == 2) {
      if (!bVar2) goto LAB_10013a85;
      memw();
      uVar6 = *puVar3 & DAT_100066c4;
      goto LAB_10013a91;
    }
    bVar1 = *PTR_DAT_10006724;
    if (bVar1 == 1) {
      memw();
      uVar6 = *puVar3 & DAT_1000628c;
LAB_10013ad8:
      memw();
      *puVar3 = uVar6;
    }
    else if (bVar1 < 2) {
      if (bVar1 == 0) {
LAB_10013acc:
        memw();
        uVar6 = *puVar3 | DAT_10005e34;
        goto LAB_10013ad8;
      }
    }
    else if (bVar1 == 2) {
      if (!bVar2) goto LAB_10013acc;
      memw();
      uVar6 = *puVar3 & DAT_1000628c;
      goto LAB_10013ad8;
    }
    bVar1 = *PTR_DAT_10006720;
    if (bVar1 == 1) {
      memw();
      uVar6 = *puVar3 & DAT_100060c0;
LAB_10013b20:
      memw();
      *puVar3 = uVar6;
    }
    else if (bVar1 < 2) {
      if (bVar1 == 0) {
LAB_10013b14:
        memw();
        uVar6 = *puVar3 | DAT_100066c8;
        goto LAB_10013b20;
      }
    }
    else if (bVar1 == 2) {
      if (!bVar2) goto LAB_10013b14;
      memw();
      uVar6 = *puVar3 & DAT_100060c0;
      goto LAB_10013b20;
    }
    bVar2 = (bool)(bVar2 ^ 1);
    threadx_sleep_candidate(uVar5 >> 1);
  } while( true );
}
