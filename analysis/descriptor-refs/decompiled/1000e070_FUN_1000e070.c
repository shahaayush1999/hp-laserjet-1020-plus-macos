/* Function: 1000e070 FUN_1000e070 */


void FUN_1000e070(int param_1)

{
  int iVar1;
  int *piVar2;
  char *pcVar3;
  uint uVar4;
  char cVar5;
  char *pcVar6;
  char *pcVar7;
  bool bVar8;
  int local_30 [12];
  
  uVar4 = *(uint *)(param_1 + 0xc);
  if (uVar4 == 2) {
    if (*(int *)(PTR_DAT_10006288 + 0xa8) == 2) {
      if (*(int *)(param_1 + 0x10) == 0) {
        FUN_1001693c(param_1 + 0x1d,PTR_DAT_100062ac);
        if (*(char *)(param_1 + 0x1c) != '\0') {
          FUN_1000dda8(10);
        }
        *(undefined1 *)(param_1 + 0x1c) = 1;
        return;
      }
      piVar2 = *(int **)(param_1 + 0x14);
      bVar8 = false;
      if (piVar2 != (int *)0x0) {
        do {
          iVar1 = FUN_1001684c(piVar2[1],PTR_DAT_100062ac);
          if (iVar1 == 0) {
            *(int *)(param_1 + 0x74) = piVar2[2];
            if (*(char *)(param_1 + 0x1c) != '\0') {
              FUN_1000dda8(10);
            }
            bVar8 = true;
            *(undefined1 *)(param_1 + 0x1c) = 1;
          }
          piVar2 = (int *)*piVar2;
        } while ((piVar2 != (int *)0x0) && (!bVar8));
      }
      if (bVar8) {
        return;
      }
      FUN_1000dda8(0x10);
      return;
    }
  }
  else if (uVar4 < 3) {
    if (uVar4 != 1) {
      return;
    }
    if (*(int *)(PTR_DAT_10006288 + 0xa8) == 1) {
      FUN_1001693c(param_1 + 0x1d,PTR_DAT_100062ac);
      if (*(char *)(param_1 + 0x1c) != '\0') {
        FUN_1000dda8(10);
      }
      *(undefined1 *)(param_1 + 0x1c) = 1;
      return;
    }
  }
  else {
    if (uVar4 != 6) {
      return;
    }
    bVar8 = false;
    if (*(int *)(PTR_DAT_10006288 + 0xa8) == 7) {
      cVar5 = *PTR_DAT_100062ac;
      pcVar6 = PTR_DAT_100062ac;
      while (cVar5 != '\0') {
        if (cVar5 == '.') goto LAB_1000e149;
        pcVar6 = pcVar6 + 1;
        cVar5 = *pcVar6;
      }
      pcVar3 = (char *)0x0;
      pcVar7 = pcVar6;
      if (*pcVar6 == '.') {
LAB_1000e149:
        pcVar7 = pcVar6 + 1;
        pcVar3 = pcVar6;
      }
      cVar5 = *pcVar7;
      if (cVar5 != '\0') {
        do {
          if (cVar5 == '0') {
            pcVar7 = pcVar7 + 1;
          }
          else {
            bVar8 = true;
          }
          cVar5 = *pcVar7;
        } while ((cVar5 != '\0') && (!bVar8));
      }
      if (bVar8) {
        FUN_1000dda8(0xc);
      }
      if (pcVar3 != (char *)0x0) {
        *pcVar3 = '\0';
      }
    }
    if (1 < *(int *)(PTR_DAT_10006288 + 0xa8) - 1U) {
      iVar1 = FUN_1000d5b0(PTR_DAT_100062ac,local_30);
      bVar8 = false;
      if ((*(int *)(param_1 + 0x18) < local_30[0]) || (local_30[0] < *(int *)(param_1 + 0x14))) {
        bVar8 = true;
      }
      if ((!bVar8) && (iVar1 != 1)) {
        if (iVar1 == 2) {
          FUN_1000dda8(0xc);
          return;
        }
        if (*(char *)(param_1 + 0x1c) != '\0') {
          FUN_1000dda8(10);
        }
        *(undefined1 *)(param_1 + 0x1c) = 1;
        *(int *)(param_1 + 0x70) = local_30[0];
        return;
      }
      FUN_1000dda8(0xe);
      return;
    }
  }
  FUN_1000dda8(8);
  return;
}


