import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { AppMaterialModule } from './modules/material.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { AppRoutingModule } from './modules/app-routing.module';
import { HeaderComponent } from './components/header/header.component';
<<<<<<< HEAD
import { MatToolbarModule } from '@angular/material/toolbar';
=======
>>>>>>> develop
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { GridComponent } from './components/grid/grid.component';
import { GridFooterComponent } from './components/grid-footer/grid-footer.component';
import { InformationsComponent } from './components/informations/informations.component';
import { GraphsComponent } from './components/graphs/graphs.component';
import { TimestampComponent } from './components/timestamp/timestamp.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSliderModule } from '@angular/material/slider';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    SidebarComponent,
    GridComponent,
    GridFooterComponent,
    InformationsComponent,
    GraphsComponent,
    TimestampComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MatToolbarModule,
    MatFormFieldModule,
    MatSelectModule,
    MatCheckboxModule,
    MatSliderModule,
    MatInputModule,
    MatIconModule,
    FormsModule, 
    ReactiveFormsModule,
    AppRoutingModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
