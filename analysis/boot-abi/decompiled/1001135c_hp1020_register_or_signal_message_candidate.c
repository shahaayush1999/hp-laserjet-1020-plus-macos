/* Function: 1001135c hp1020_register_or_signal_message_candidate */


/* medium confidence: Register/signal message service from system-interface table */

void hp1020_register_or_signal_message_candidate(int param_1,undefined4 param_2)

{
  undefined *puVar1;
  undefined1 *puVar2;
  int iVar3;
  
  while (puVar2 = (undefined1 *)hp1020_runtime_service_candidate(0x14,1),
        puVar2 == (undefined1 *)0x0) {
    threadx_sleep_candidate(0x14);
  }
  hp1020_datastore_lock_entry_candidate(param_1);
  if (puVar2 != (undefined1 *)0x0) {
    puVar2[8] = 0;
    puVar2[9] = 0;
    puVar2[10] = 0;
    puVar2[0xb] = 0;
    puVar2[4] = (char)((uint)param_2 >> 0x18);
    puVar2[5] = (char)((uint)param_2 >> 0x10);
    puVar2[6] = (char)((uint)param_2 >> 8);
    puVar2[7] = (char)param_2;
    *puVar2 = (char)((uint)param_1 >> 0x18);
    puVar2[1] = (char)((uint)param_1 >> 0x10);
    puVar2[2] = (char)((uint)param_1 >> 8);
    puVar1 = PTR_DAT_10006490;
    puVar2[3] = (char)param_1;
    iVar3 = *(int *)(puVar1 + param_1 * 4);
    if (iVar3 == 0) {
      *(undefined1 **)(puVar1 + param_1 * 4) = puVar2;
      FUN_1001b290(puVar2 + 0xc);
    }
    else {
      FUN_1001b2c4(iVar3 + 0xc,puVar2 + 0xc);
    }
  }
  hp1020_datastore_unlock_entry_candidate(param_1);
  return;
}


