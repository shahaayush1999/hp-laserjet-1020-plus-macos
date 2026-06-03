/*
Function: 1000cdb0 hp1020_pjl_echo_matcher
Score: 12
*/


undefined4 hp1020_pjl_echo_matcher(void)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  undefined4 uVar4;
  int iVar5;
  
  puVar2 = PTR_PTR_10006274;
  iVar3 = hp1020_strlen_like(*(undefined4 *)PTR_PTR_10006274);
  puVar1 = PTR_DAT_10006270;
  uVar4 = 0;
  iVar5 = 0;
  if (iVar3 != 0) {
    do {
      hp1020_pjl_read_or_poll_candidate();
      if (*(uint *)puVar1 == (uint)*(byte *)(*(int *)puVar2 + iVar5)) {
        iVar5 = iVar5 + 1;
      }
      else {
        if (*(uint *)puVar1 == 0xffffffff) {
          uVar4 = 0xfffffffe;
          break;
        }
        iVar5 = 0;
      }
    } while (iVar5 != iVar3);
  }
  *PTR_DAT_1000626c = 1;
  return uVar4;
}


