import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SharedService {
  public currentPage = new BehaviorSubject(1);
  currentPageCount = this.currentPage.asObservable();

  private precisionValueSelected = new BehaviorSubject(0.5);
  currentPrecisionValue = this.precisionValueSelected.asObservable();

  private squareNb = new BehaviorSubject(100);
  squareNbValue = this.squareNb.asObservable();

  columnWidths = new BehaviorSubject(`repeat(10, ${100 / 10}%)`);
  columnWidthsValue = this.columnWidths.asObservable();

  rowHeights = new BehaviorSubject(`repeat(10, ${100 / 10}%)`);
  rowHeightsValue = this.rowHeights.asObservable();

  changeSquareNb(squareNb: number) {
    this.squareNb.next(squareNb);
    const nbSquarePerLine = Math.sqrt(this.squareNb.getValue());
    this.columnWidths.next(
      `repeat(${nbSquarePerLine}, ${100 / nbSquarePerLine}%)`
    );
    this.rowHeights.next(
      `repeat(${nbSquarePerLine}, ${100 / nbSquarePerLine}%)`
    );
  }

  changeCount(currentPage: number) {
    this.currentPage.next(currentPage);
  }

  changePrecisionValue(currentPrecisionValue: number) {
    this.precisionValueSelected.next(currentPrecisionValue);
  }

  houseColor(data: number) {
    const upperBound = this.precisionValueSelected.value;
    const middleUpperBound = upperBound / 2;
    const center = 0;
    const middleLowerBound = -middleUpperBound;
    const lowerBound = -upperBound;
    const boundRange = upperBound - middleUpperBound;

    if (data < lowerBound) {
      return 'rgba(0, 0, 255, 100)';
    } else if (lowerBound <= data && data < middleLowerBound) {
      const temp = -(lowerBound - data) / boundRange;
      const color = temp * 255;
      return 'rgba(0,' + color + ', 255, 100)';
    } else if (middleLowerBound <= data && data < center) {
      const temp = (boundRange + (middleLowerBound - data)) / boundRange;
      const color = temp * 255;
      return 'rgba(0, 255,' + color + ', 100)';
    } else if (center <= data && data < middleUpperBound) {
      const temp = (boundRange - (middleUpperBound - data)) / boundRange;
      const color = temp * 255;
      return 'rgba(' + color + ',255, 0, 100)';
    } else if (middleUpperBound <= data && data <= upperBound) {
      const temp = (upperBound - data) / boundRange;
      const color = temp * 255;
      return 'rgba(255,' + color + ', 0, 100)';
    } else {
      return 'rgba(255, 0, 0, 100)';
    }
  }
}
