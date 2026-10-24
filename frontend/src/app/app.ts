import { Component } from '@angular/core';
import { ShellComponent } from './layout/shell.component';

@Component({
  imports: [ShellComponent],
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}