/* Function: 1000ed90 FUN_1000ed90 */


void FUN_1000ed90(void)

{
  ushort uVar1;
  undefined *puVar2;
  int *piVar3;
  ushort uVar4;
  int *piVar5;
  int iVar6;
  int iVar7;
  undefined4 local_30 [3];
  undefined4 uStack_24;

  puVar2 = PTR_DAT_100062e8;
  piVar3 = *(int **)PTR_DAT_100062e4;
  uVar4 = 0;
  do {
    if ((piVar3 == (int *)0x0) || (*(short *)puVar2 == 0)) {
      return;
    }
    piVar5 = *(int **)(piVar3[3] + 0x70);
    while ((piVar5 != (int *)0x0 && (*(short *)puVar2 != 0))) {
      iVar6 = piVar5[3];
      iVar7 = *(int *)(iVar6 + 0x48);
      if ((iVar7 != 0) &&
         ((*(ushort *)(iVar7 + 0x48) != *(ushort *)(iVar7 + 0xc) &&
          (*(char *)(iVar7 + 0x78) != '\0')))) {
        uVar1 = *(ushort *)(iVar7 + 0xc);
        if (uVar4 < uVar1) {
          uVar4 = uVar1;
        }
        if (*(ushort *)(iVar7 + 0x48) != uVar1) {
          do {
            if (*(short *)puVar2 == 0) break;
            *(short *)puVar2 = *(short *)puVar2 + -1;
            *(short *)(iVar7 + 0x48) = *(short *)(iVar7 + 0x48) + 1;
            local_30[0] = 0xb;
            uStack_24 = *(undefined4 *)(iVar6 + 0x48);
            hp1020_queue_send_candidate(1,local_30);
          } while (*(short *)(iVar7 + 0x48) != *(short *)(iVar7 + 0xc));
        }
      }
      iVar7 = *(int *)(iVar6 + 0x4c);
      if (((iVar7 != 0) && (*(ushort *)(iVar7 + 0x48) != *(ushort *)(iVar7 + 0xc))) &&
         (*(short *)puVar2 != 0)) {
        uVar1 = *(ushort *)(iVar7 + 0xc);
        if (uVar4 < uVar1) {
          uVar4 = uVar1;
        }
        if (*(ushort *)(iVar7 + 0x48) != uVar1) {
          do {
            if (*(short *)puVar2 == 0) break;
            *(short *)puVar2 = *(short *)puVar2 + -1;
            *(short *)(iVar7 + 0x48) = *(short *)(iVar7 + 0x48) + 1;
            local_30[0] = 0xb;
            uStack_24 = *(undefined4 *)(iVar6 + 0x4c);
            hp1020_queue_send_candidate(1,local_30);
          } while (*(short *)(iVar7 + 0x48) != *(short *)(iVar7 + 0xc));
        }
      }
      piVar5 = (int *)*piVar5;
    }
    piVar3 = (int *)*piVar3;
  } while( true );
}
