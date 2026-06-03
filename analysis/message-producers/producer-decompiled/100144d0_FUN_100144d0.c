/* Function: 100144d0 FUN_100144d0 */


void FUN_100144d0(int param_1)

{
  undefined *puVar1;
  uint *puVar2;
  uint *puVar3;
  uint uVar4;
  int iVar5;
  undefined4 uVar6;
  bool in_b8;
  
  puVar3 = DAT_100067d8;
  puVar2 = DAT_100067c0;
  puVar1 = PTR_DAT_10006770;
  memw();
  if (((*DAT_100067c0 & 0x20) != 0) || (memw(), (*DAT_100067d8 & 0x20) != 0)) {
    memw();
    uVar4 = *DAT_100067c0;
    *(int *)(PTR_DAT_10006770 + 0xf8) = *(int *)(PTR_DAT_10006770 + 0xf8) + 1;
    if ((uVar4 & 0x20) != 0) {
      memw();
      *puVar2 = 0xffffffdf;
    }
    memw();
    if ((*DAT_100067d8 & 0x20) != 0) {
      memw();
      *DAT_100067d8 = 0xffffffdf;
    }
    if (*(int *)(puVar1 + 0xfc) < 0) {
      iVar5 = *(int *)(*(int *)(puVar1 + 0xa0) + 0xc);
      if (*(short *)(iVar5 + 0x4e) != 0) {
        if (*(int *)(iVar5 + 0x54) != 0) {
          *(int *)(iVar5 + 0x54) = *(int *)(iVar5 + 0x54) + -0x10;
        }
        puVar1 = PTR_DAT_100062dc;
        *(short *)(iVar5 + 0x4e) = *(short *)(iVar5 + 0x4e) + -1;
        FUN_10017dac(puVar1,8,0);
      }
      *(undefined4 *)(PTR_DAT_10006770 + 0xa0) = **(undefined4 **)(PTR_DAT_10006770 + 0xa0);
      FUN_100140f8();
    }
    else {
      *(undefined4 *)(puVar1 + *(int *)(puVar1 + 0xd8) * 0xc + 0x20) = 0;
      *(uint *)(puVar1 + 0xd8) = *(int *)(puVar1 + 0xd8) + 1U & 3;
      FUN_10014244();
      FUN_10013f34();
    }
    *(undefined4 *)(PTR_DAT_10006770 + 0xf0) = 1;
    goto LAB_1001471b;
  }
  memw();
  if ((*DAT_100067c0 & 2) == 0) {
    memw();
    uVar6 = 4;
    if ((*DAT_100067c0 & 4) != 0) {
      memw();
      *DAT_100067c0 = 0xfffffffb;
      iVar5 = *(int *)(puVar1 + 0x70);
      memw();
      *puVar3 = 0xfffffffb;
      puVar3 = DAT_10006808;
      if (iVar5 != 0) {
        if (*(int *)(puVar1 + 0x6c) != 0) {
          if (*(int *)(puVar1 + 0xf0) == 0) {
            *(undefined4 *)(puVar1 + 0xdc) = 0;
            memw();
            memw();
            *puVar3 = *puVar3 & 0xfffffeff;
            puVar3 = DAT_1000680c;
            memw();
            uVar4 = *puVar2;
            while ((uVar4 & 0x200) != 0) {
              memw();
              uVar4 = *puVar2;
            }
            memw();
            memw();
            *DAT_10006808 = *DAT_10006808 | 0x100;
            puVar2 = DAT_100067d8;
            memw();
            memw();
            *puVar3 = *puVar3 & 0xfffffeff;
            memw();
            uVar4 = *puVar2;
            while ((uVar4 & 0x200) != 0) {
              memw();
              uVar4 = *puVar2;
            }
            if (*(int *)PTR_DAT_100067c8 == 1) {
              memw();
              memw();
              *DAT_1000680c = *DAT_1000680c | 0x100;
            }
            if (in_b8) {
              FUN_100140f8();
            }
            else {
              FUN_10013f34();
            }
          }
          else {
            hp1020_video_reset_dispatch_candidate(0);
          }
        }
        puVar1 = PTR_DAT_10006810;
        *(undefined4 *)(PTR_DAT_10006770 + 0x70) = 0;
        FUN_10018214(puVar1);
      }
      goto LAB_1001471b;
    }
    memw();
    if (((*DAT_100067c0 & 1) != 0) || (memw(), (*DAT_100067d8 & 1) != 0)) {
      memw();
      if ((*DAT_100067c0 & 1) != 0) {
        memw();
        *DAT_100067c0 = 0xfffffffe;
      }
      memw();
      if ((*puVar3 & 1) != 0) {
        memw();
        *puVar3 = 0xfffffffe;
      }
      puVar1 = PTR_DAT_10006770;
      if (*(int *)(PTR_DAT_10006770 + 0x6c) == 0) {
        hp1020_video_reset_dispatch_candidate(7);
        FUN_100181a4(PTR_DAT_10006810,0);
      }
      *(undefined4 *)(puVar1 + 0x70) = 1;
      goto LAB_1001471b;
    }
    memw();
    if (((*DAT_100067c0 & 8) == 0) && (memw(), (*DAT_100067d8 & 8) == 0)) {
      memw();
      if (((*DAT_100067c0 & 0x10) == 0) &&
         ((*(int *)PTR_DAT_100067c8 != 1 || (memw(), (*DAT_100067d8 & 0x10) == 0))))
      goto LAB_1001471b;
      uVar4 = 0xffffffef;
      goto LAB_1001470c;
    }
    memw();
    *DAT_100067c0 = 0xfffffff7;
    memw();
    *puVar3 = 0xfffffff7;
    uVar6 = 3;
  }
  else {
    uVar4 = 0xfffffffd;
    uVar6 = 0;
LAB_1001470c:
    memw();
    *DAT_100067c0 = uVar4;
    memw();
    *puVar3 = uVar4;
  }
  hp1020_video_reset_dispatch_candidate(uVar6);
LAB_1001471b:
  if (param_1 == 10) {
    FUN_100171e0(10);
  }
  if (param_1 == 0xb) {
    FUN_100171e0(0xb);
  }
  return;
}


