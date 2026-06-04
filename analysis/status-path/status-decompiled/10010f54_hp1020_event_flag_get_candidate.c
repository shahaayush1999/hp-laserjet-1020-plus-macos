/* Function: 10010f54 hp1020_event_flag_get_candidate */


/* medium confidence: Event flag get from system-interface table */

void hp1020_event_flag_get_candidate(int *param_1)

{
  undefined *puVar1;
  int iVar2;
  
  puVar1 = PTR_DAT_1000647c;
  iVar2 = *param_1;
  FUN_100111b4(iVar2);
  if (param_1[1] != 0) {
    switch(*(undefined4 *)(puVar1 + *param_1 * 0x18 + 8)) {
    case 0:
      *(undefined1 *)param_1[1] = **(undefined1 **)(puVar1 + iVar2 * 0x18 + 4);
      break;
    case 1:
      *(undefined2 *)param_1[1] = **(undefined2 **)(puVar1 + iVar2 * 0x18 + 4);
      break;
    case 2:
      *(undefined4 *)param_1[1] = **(undefined4 **)(puVar1 + iVar2 * 0x18 + 4);
      break;
    case 3:
      FUN_10016a38(param_1[1],*(undefined4 *)(puVar1 + iVar2 * 0x18 + 4),
                   *(undefined2 *)(puVar1 + iVar2 * 0x18 + 0x10));
      break;
    case 4:
      FUN_1001b38c(param_1[1],*(undefined4 *)(puVar1 + iVar2 * 0x18 + 4),
                   *(undefined2 *)(puVar1 + iVar2 * 0x18 + 0x10));
    }
  }
  return;
}


