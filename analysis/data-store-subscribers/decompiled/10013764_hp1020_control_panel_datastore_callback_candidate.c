/* Function: 10013764 hp1020_control_panel_datastore_callback_candidate */


/* data-store subscriber mapping candidate */

void hp1020_control_panel_datastore_callback_candidate(int param_1,uint param_2)

{
  uint uVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined1 uVar4;
  uint uVar5;
  undefined *puVar6;

  puVar6 = PTR_DAT_1000671c;
  puVar2 = PTR_DAT_10006718;
  if (*(int *)PTR_DAT_10006718 != 0) {
    FUN_10018304(PTR_DAT_1000671c);
    FUN_1001839c(puVar6);
    *(undefined4 *)puVar2 = 0;
  }
  puVar6 = PTR_DAT_10006724;
  puVar2 = PTR_DAT_10006720;
  uVar1 = DAT_10006358;
  if (param_1 == 0x18) {
    *PTR_DAT_10006720 = 0;
    *puVar6 = 0;
    if (param_2 == 1) {
      *PTR_DAT_10006728 = 1;
    }
    else {
      *PTR_DAT_10006728 = 0;
    }
  }
  else if (param_1 == 0x19) {
    *PTR_DAT_10006720 = 0;
    *puVar6 = 0;
    uVar5 = param_2 & uVar1;
    if (uVar5 == uVar1) {
      uVar4 = 1;
      *puVar6 = 1;
      puVar6 = PTR_DAT_10006728;
      *puVar2 = 1;
    }
    else {
      if (uVar5 == DAT_1000635c) {
        *puVar6 = 2;
        *puVar2 = 0;
        puVar3 = PTR_DAT_10006728;
        uVar1 = DAT_10005c88;
        *PTR_DAT_10006728 = 0;
        if ((param_2 & uVar1) == 0) {
          return;
        }
        *puVar6 = 2;
        *puVar3 = 0;
        *puVar2 = 0;
        return;
      }
      if (param_2 == DAT_100063ec) {
        uVar4 = 2;
        *puVar6 = 2;
        puVar6 = PTR_DAT_10006728;
        *puVar2 = 2;
      }
      else if (param_2 == DAT_1000640c) {
        *puVar6 = 0;
        puVar6 = PTR_DAT_10006728;
        uVar4 = 2;
        *puVar2 = 2;
      }
      else {
        if (param_2 == DAT_10006048) {
          *puVar6 = 2;
          puVar6 = PTR_DAT_10006728;
          *puVar2 = 0;
          *puVar6 = 2;
          return;
        }
        if ((param_2 & DAT_10005f74) == DAT_10006418) {
          *puVar6 = 0;
          *puVar2 = 0;
          uVar4 = 2;
          puVar6 = PTR_DAT_10006728;
        }
        else {
          if ((param_2 & DAT_10005f74) != 0x100) {
            return;
          }
          *puVar6 = 0;
          *puVar2 = 0;
          uVar4 = 1;
          puVar6 = PTR_DAT_10006728;
        }
      }
    }
    *puVar6 = uVar4;
  }
  return;
}
