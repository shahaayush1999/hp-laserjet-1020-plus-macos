/* Function: 1000da5c FUN_1000da5c */


void FUN_1000da5c(void)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined4 uVar3;
  int iVar4;
  
  puVar1 = PTR_DAT_10006288;
  *PTR_DAT_10006288 = 0;
  *(undefined4 *)(puVar1 + 0xa4) = 0;
  puVar1[0x51] = 0;
  *(undefined4 *)(puVar1 + 0xa8) = 0;
  *(undefined4 *)(puVar1 + 0xac) = 0;
  uVar3 = FUN_1000d9b0(puVar1,1);
  *(undefined4 *)(puVar1 + 0xa4) = uVar3;
  puVar2 = PTR_DAT_10006288;
  puVar1 = PTR_DAT_1000626c;
  switch(uVar3) {
  case 1:
    *(undefined4 *)(PTR_DAT_10006288 + 0xac) = 0x14;
    break;
  case 2:
    iVar4 = *(int *)(PTR_DAT_10006288 + 0xa4);
    while (iVar4 == 2) {
      if (*puVar1 == '\0') {
        FUN_1000d6b0();
        iVar4 = *(int *)PTR_DAT_10006270;
        if ((iVar4 != 0x20) && (iVar4 != 9)) {
          if (iVar4 == 0x3a) {
            *(undefined4 *)(puVar2 + 0xa4) = 4;
          }
          else if (iVar4 == 0x3d) {
            *(undefined4 *)(puVar2 + 0xa4) = 3;
          }
          else if (iVar4 < 0x21) {
            if (*puVar1 == '\0') {
              *(undefined4 *)(puVar2 + 0xa4) = 0;
              *(undefined4 *)(puVar2 + 0xac) = 6;
              if (iVar4 != -1) goto LAB_1000db12;
            }
            else {
              *(undefined4 *)(puVar2 + 0xa4) = 5;
            }
          }
          else {
            *(undefined4 *)(puVar2 + 0xa4) = 5;
LAB_1000db12:
            FUN_1000dd60();
          }
        }
      }
      else {
        *(undefined4 *)(PTR_DAT_10006288 + 0xa4) = 5;
      }
      iVar4 = *(int *)(PTR_DAT_10006288 + 0xa4);
    }
    break;
  case 6:
  case 7:
    *(undefined4 *)(PTR_DAT_10006288 + 0xac) = 0x13;
  }
  puVar2 = PTR_DAT_100062ac;
  puVar1 = PTR_DAT_10006288;
  if (*(int *)(PTR_DAT_10006288 + 0xa4) == 3) {
    iVar4 = FUN_1000d9b0(PTR_DAT_100062ac,0);
    *(int *)(puVar1 + 0xa8) = iVar4;
    if ((iVar4 == 0) && (*(int *)(puVar1 + 0xac) == 0)) {
      *(undefined4 *)(puVar1 + 0xac) = 0xf;
    }
  }
  else if (*(int *)(PTR_DAT_10006288 + 0xa4) == 4) {
    if (*(int *)PTR_DAT_1000629c == 0) {
      *(undefined4 *)PTR_DAT_1000629c = 1;
      iVar4 = FUN_1000d9b0(puVar2);
      *(int *)(puVar1 + 0xa8) = iVar4;
      if (iVar4 == 2) {
        return;
      }
      if (*(int *)(puVar1 + 0xac) != 0) {
        return;
      }
    }
    else {
      if (*(int *)PTR_DAT_1000629c == 1) {
        *(undefined4 *)(PTR_DAT_10006288 + 0xac) = 0x10;
        return;
      }
      iVar4 = FUN_1000d9b0(PTR_DAT_100062ac,0);
      *(int *)(puVar1 + 0xa8) = iVar4;
      if ((iVar4 == 2) || (*(int *)(puVar1 + 0xac) != 0)) {
        *(undefined4 *)(PTR_DAT_10006288 + 0xac) = 0x11;
        return;
      }
    }
    *(undefined4 *)(puVar1 + 0xac) = 0xe;
    return;
  }
  *(undefined4 *)PTR_DAT_1000629c = 2;
  return;
}


