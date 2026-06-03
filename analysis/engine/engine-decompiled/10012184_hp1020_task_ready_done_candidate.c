/* Function: 10012184 hp1020_task_ready_done_candidate */


void hp1020_task_ready_done_candidate(int param_1)

{
  char cVar1;
  undefined4 uVar2;
  
  uVar2 = 1;
  if (param_1 == 1) {
    cVar1 = *PTR_DAT_1000654c + -1;
    *PTR_DAT_1000654c = cVar1;
  }
  else {
    if (param_1 != 0) {
      if ((param_1 == 2) &&
         (cVar1 = *PTR_DAT_10006550, *PTR_DAT_10006550 = cVar1 + -1, (char)(cVar1 + -1) == '\0')) {
        uVar2 = 4;
      }
      goto LAB_100121d4;
    }
    cVar1 = *PTR_DAT_1000654c;
  }
  if ((cVar1 == '\0') && (uVar2 = 4, *PTR_DAT_10006550 != '\0')) {
    uVar2 = 2;
  }
LAB_100121d4:
  FUN_10017dac(PTR_DAT_10006530,uVar2,0);
  return;
}


