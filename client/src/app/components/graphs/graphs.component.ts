import { Component, AfterViewInit, ViewChild, ViewChildren, QueryList, ElementRef } from '@angular/core';
import { SimulationManagerService } from '@app/services/simulation-manager.service';
import { Chart, ChartConfiguration, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import zoomPlugin from 'chartjs-plugin-zoom';
Chart.register(zoomPlugin);

@Component({ 
  selector: 'app-graphs',
  templateUrl: './graphs.component.html',
  styleUrls: ['./graphs.component.scss']
})
export class GraphsComponent implements AfterViewInit {
  constructor(
    public sms: SimulationManagerService,
  ) {
  }

  @ViewChildren(BaseChartDirective)
  charts!: QueryList<BaseChartDirective>

  @ViewChild("aaa", { static: false })
  chartOne!: BaseChartDirective

  @ViewChild("bbb", { static: false })
  chartTwo!: BaseChartDirective

  @ViewChild("ccc", { static: false })
  chartThree!: BaseChartDirective

  ngAfterViewInit(): void {
    // we HAVE to go though a subscribe because we need to call chart.update() to update the chart
    this.sms.sidenavObservable.subscribe((data) => {
      {
        //First graph
        const categories = ['Current consumption', 'Regulation signal'];
        let datasets = categories.map((category) => {
          return {
            data: data.map((elem) => Number(elem[category])),
            label: category,
            fill: false,
            tension: 0,
            borderColor: ['blue', 'white'],
            backgroundColor: ['blue', 'white'],
            pointBackgroundColor: 'black',
            pointRadius: 0,
            pointHoverRadius: 15,
          }
        }
        );
        this.lineChartData.datasets = datasets;
        this.lineChartData.labels = Array.from(Array(data.length).keys());
      };
      {
        //Second graph
        const categories = ['Average temperature error', 'Average temperature difference'];
        let datasets = categories.map((category) => {
          return {
            data: data.map((elem) => Number(elem[category])),
            label: category,
            fill: false,
            tension: 0,
            borderColor: ['green', 'orange'],
            backgroundColor: ['green', 'orange'],
            pointBackgroundColor: 'black',
            pointRadius: 0,
            pointHoverRadius: 15,
          }
        }
        );
        this.lineChartData2.datasets = datasets;
        this.lineChartData2.labels = Array.from(Array(data.length).keys());
      };
      {
        //Third graph
        const categories = ['Outdoor temperature', 'Mass temperature', 'Target temperature'];
        let datasets = categories.map((category) => {
          return {
            data: data.map((elem) => Number(elem[category])),
            label: category,
            fill: false,
            tension: 0,
            borderColor: ['purple', 'red', 'yellow'],
            backgroundColor: ['purple', 'red', 'yellow'],
            pointBackgroundColor: 'black',
            pointRadius: 0,
            pointHoverRadius: 15,
          }
        }
        );
        this.lineChartData3.datasets = datasets;
        this.lineChartData3.labels = Array.from(Array(data.length).keys());
      };
      this.chartOne.chart!.update('none');
      this.chartTwo.chart!.update('none');
      this.chartThree.chart!.update('none');
    })
  }

  //First Graph
  public lineChartData: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        label: 'Average temperature difference',
        fill: false,
        tension: 0,
        borderColor: 'black',
        backgroundColor: 'rgba(255,0,0,0.3)'
      }
    ]
  };

  //Second graph
  public lineChartData2: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        label: 'Average indoor temperature',
        fill: false,
        tension: 0,
        borderColor: 'black',
        backgroundColor: 'rgba(0,0,255,0.3)'
      }
    ],

  };

  //Third graph
  public lineChartData3: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: [
      {
        data: [],
        label: 'Outdoor temperature',
        fill: false,
        tension: 0,
        borderColor: 'black',
        backgroundColor: 'rgba(0,0,255,0.3)'
      }
    ],

  };

  //Graphs options
  public lineChartOptions: ChartOptions<'line'> = {
    responsive: true,
    display: true,
    align: 'center',

    plugins: {
      zoom: {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x',
        },
        pan: {
          enabled: true,
          mode: 'xy',
        }
      },
      legend: {
        display: true,
        labels: {
            color: 'black',
            boxWidth: 5,
            boxHeight: 5,
        }
    }
    }
  } as ChartOptions<'line'>;

  public lineChartLegend = true;

  public resetZoomGraph(index: number): void {
    // The code(this.charts.get(index)!.chart as any).resetZoom() is likely used to reset the zoom level of a chart.this.charts.get(index)
    // is used to get a reference to the chart object at the specified index. .chart as 
    // any is used to cast the chart object to any type, which allows accessing the resetZoom() method.
    // The resetZoom() method is then called to reset the zoom level of the chart.
    (this.charts.get(index)!.chart as any).resetZoom()
  }
}
