/* Function: 10010a8c hp1020_status_event_store_candidate */


void hp1020_status_event_store_candidate(undefined4 param_1)

{
  undefined *puVar1;
  int iVar2;
  uint uVar3;
  
  puVar1 = PTR_DAT_1000642c;
  iVar2 = *(int *)PTR_DAT_1000642c;
  *(undefined4 *)(PTR_DAT_10006428 + iVar2 * 4) = param_1;
  uVar3 = iVar2 + 1;
  *(uint *)puVar1 = uVar3;
  if (99 < uVar3) {
    *(undefined4 *)puVar1 = 0;
  }
  return;
}


