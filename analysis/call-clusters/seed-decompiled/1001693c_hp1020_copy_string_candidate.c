/* Function: 1001693c hp1020_copy_string_candidate */


/* WARNING: Control flow encountered bad instruction data */

void hp1020_copy_string_candidate(char *param_1,char *param_2)

{
  char cVar1;
  
  if (((uint)param_2 & 1) != 0) {
    cVar1 = *param_2;
    param_2 = param_2 + 1;
    *param_1 = cVar1;
    if (cVar1 == '\0') {
      return;
    }
    param_1 = param_1 + 1;
  }
  if (((uint)param_2 & 2) != 0) {
    cVar1 = *param_2;
    *param_1 = cVar1;
    if (cVar1 != '\0') {
      cVar1 = param_2[1];
      param_1[1] = cVar1;
      param_1 = param_1 + 2;
      if (cVar1 != '\0') goto LAB_10016954;
    }
    return;
  }
LAB_10016954:
  if (((uint)param_1 & 3) == 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


