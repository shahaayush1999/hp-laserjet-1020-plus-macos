/* Function: 100116ec hp1020_system_service_candidate */


/* low confidence: System service from system-interface table */

void hp1020_system_service_candidate(int param_1)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  
  uVar1 = FUN_1001bb5c();
  uVar2 = uVar1 + param_1 * (uint)*(ushort *)PTR_DAT_10005dfc;
  if (uVar2 < uVar1) {
    do {
      do {
        uVar3 = FUN_1001bb5c();
      } while (uVar3 < uVar2);
      uVar3 = FUN_1001bb5c();
    } while (uVar1 < uVar3);
  }
  else {
    do {
      uVar3 = FUN_1001bb5c();
      if (uVar2 <= uVar3) {
        return;
      }
      uVar3 = FUN_1001bb5c();
    } while (uVar1 < uVar3);
  }
  return;
}


