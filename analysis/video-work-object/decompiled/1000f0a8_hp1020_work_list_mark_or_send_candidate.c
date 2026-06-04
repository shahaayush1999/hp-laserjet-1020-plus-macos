/* Function: 1000f0a8 hp1020_work_list_mark_or_send_candidate */


undefined4 hp1020_work_list_mark_or_send_candidate(int *param_1,int param_2)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  int iVar4;
  uint uVar5;

  uVar5 = 0;
  uVar1 = 0;
  if (param_1 == (int *)0x0) {
    return uVar1;
  }
  puVar2 = (undefined4 *)*param_1;
  if (puVar2 == (undefined4 *)0x0) {
    return uVar1;
  }
  iVar4 = puVar2[3];
LAB_1000f0bd:
  do {
    puVar3 = puVar2;
    if (param_2 != 2) goto LAB_1000f0cb;
    do {
      puVar3 = puVar2;
      if (*(short *)(iVar4 + 0x4e) != 0) {
        *(short *)(iVar4 + 0x4e) = *(short *)(iVar4 + 0x4e) + -1;
      }
LAB_1000f0cb:
      if (param_2 == 3) {
        *(undefined2 *)(iVar4 + 0x4e) = 1;
      }
      if ((*(short *)(iVar4 + 0x4e) == 0) || (param_2 == 1)) {
        uVar1 = rsil(1);
        uVar5 = uVar5 & 0xffffcfff;
        hp1020_list_pop_head_candidate(param_1);
        wsr((char)uVar5,uVar1);
        rsync();
        if (*(int *)(iVar4 + 0x50) != 2) {
          uVar5 = uVar5 & 0xffffcfff;
          FUN_10013408(*(undefined4 *)(iVar4 + 0x54));
        }
        puVar2 = (undefined4 *)*puVar3;
        uVar5 = uVar5 & 0xffffcfff;
        FUN_10013408(puVar3);
        uVar1 = 1;
      }
      else {
        puVar2 = (undefined4 *)*puVar3;
      }
      if (puVar2 == (undefined4 *)0x0) {
        return uVar1;
      }
      iVar4 = puVar2[3];
      if ((*(short *)(iVar4 + 0x4e) == 0) || (param_2 == 1)) goto LAB_1000f0bd;
    } while (param_2 == 2);
    if (param_2 != 3) {
      return uVar1;
    }
  } while( true );
}
