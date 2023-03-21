import { Component } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { SharedService } from '@app/services/shared/shared.service';
import { SimulationManagerService } from '@app/services/simulation-manager.service';

interface Filter {
  id: number;
  type: string;
  value?: any;
}
@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
  precisionValueSelected = 0.5;
  negMin = -0.5;
  negMidMin = -0.25;
  mid = 0;
  posMidMax = 0.25;
  posMax = 0.5;

  numberFormControl = new FormControl('', [Validators.required, Validators.min(0)]);

  nbSquares = 100;
  nbSquareOptions = [25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256];
  
  constructor(public sharedService: SharedService, public simulationManager: SimulationManagerService) {
    this.simulationManager.originalHousesData = this.simulationManager.housesData.slice(); // deep copy
  }

  ngOnInit() {
    this.sharedService.currentPrecisionValue.subscribe(houseColorPrecisionValue => this.precisionValueSelected = houseColorPrecisionValue);
    this.sharedService.squareNbValue.subscribe(nbSquares => this.nbSquares = nbSquares);
  }

  formatLabel(value: number): string {
    return `${value}`;
  }

  // tempCheckbox(): void {
  //   this.isTempChecked = !this.isTempChecked;
  // }

  // floorCheckbox(): void {
  //   this.isFloorChecked = !this.isFloorChecked;
  // }

  scaleChartPrecision(): void {
    const precisionValue = (<HTMLInputElement>document.getElementById("precisionValue")).value;
    this.sharedService.changePrecisionValue(parseFloat(precisionValue));
    if(this.precisionValueSelected >= 0){
      this.negMin = -(this.precisionValueSelected);
      this.negMidMin = this.negMin / 2;
      this.posMax = Math.abs(this.precisionValueSelected);
      this.posMidMax = this.posMax / 2
      console.log("precision: %d", this.precisionValueSelected)
    }
  }

  setSquareNb(event: Event): void {
    this.sharedService.changeSquareNb(Number(event));
    this.sharedService.changeCount(1);
  }

}
