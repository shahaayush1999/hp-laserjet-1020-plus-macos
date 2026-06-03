/* Function: 10016a38 FUN_10016a38 */


/* WARNING: Control flow encountered bad instruction data */

void FUN_10016a38(char *param_1,char *param_2,int param_3)

{
  char cVar1;
  int iVar2;
  char *pcVar3;
  
  if (param_3 == 0) {
    return;
  }
  if (((uint)param_2 & 1) == 0) {
joined_r0x10016a6e:
    pcVar3 = param_1;
    if (((uint)param_2 & 2) == 0) {
LAB_10016a52:
      if (((uint)pcVar3 & 3) != 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
    cVar1 = *param_2;
    iVar2 = param_3 + -1;
    *param_1 = cVar1;
    if (iVar2 == 0) {
      return;
    }
    pcVar3 = param_1 + 1;
    if (cVar1 != '\0') {
      cVar1 = param_2[1];
      *pcVar3 = cVar1;
      iVar2 = param_3 + -2;
      if (iVar2 == 0) {
        return;
      }
      pcVar3 = param_1 + 2;
      if (cVar1 != '\0') goto LAB_10016a52;
    }
  }
  else {
    cVar1 = *param_2;
    param_2 = param_2 + 1;
    *param_1 = cVar1;
    iVar2 = param_3 + -1;
    if (iVar2 == 0) {
      return;
    }
    pcVar3 = param_1 + 1;
    param_3 = iVar2;
    param_1 = pcVar3;
    if (cVar1 != '\0') goto joined_r0x10016a6e;
  }
  if (((uint)pcVar3 & 1) != 0) {
    *pcVar3 = '\0';
    iVar2 = iVar2 + -1;
    if (iVar2 == 0) {
      return;
    }
    pcVar3 = pcVar3 + 1;
  }
  if (((uint)pcVar3 & 2) != 0) {
    *pcVar3 = '\0';
    if (iVar2 != 1) {
      pcVar3[1] = '\0';
      iVar2 = iVar2 + -2;
      if (iVar2 != 0) {
        pcVar3 = pcVar3 + 2;
        goto LAB_10016a9c;
      }
    }
    return;
  }
LAB_10016a9c:
  if (iVar2 < 4) {
    do {
      *pcVar3 = '\0';
      iVar2 = iVar2 + -1;
      pcVar3 = pcVar3 + 1;
    } while (iVar2 != 0);
    return;
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


