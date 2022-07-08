# Angular

## angular 8

@Input() 从父级传入 = react props

### [Glossary](https://v8.angular.io/guide/glossary)

### Component

```js
@Component({
  selector: 'tsl-datepicker', // The CSS selector that identifies this directive in a template and triggers instantiation of the directive.
  templateUrl: './datepicker.html', // The relative path or absolute URL of a template file for an Angular component. If provided, do not supply an inline template using template.
  styleUrls: ['./datepicker.scss'], // One or more relative paths or absolute URLs for files containing CSS stylesheets to use in this component.
  host: {
    'class': 'tsl-datepicker',
    '[class.tsl-disabled]': 'disabled',
    '(focus)': '_onFocus()',
    '(blur)': '_onBlur()'
  }, // Maps class properties to host element bindings for properties, attributes, and events, using a set of key-value pairs.
  encapsulation: ViewEncapsulation.None, // An encapsulation policy for the template and CSS styles.
  changeDetection: ChangeDetectionStrategy.OnPush, // The change-detection strategy to use for this component.
  providers: [
    { provide: TslFormFieldControl, useExisting: TslDatePicker }
  ] // Configures the injector of this directive or component with a token that maps to a provider of a dependency.
})
```

### Model

帮助开发者组织业务代码

```js
// https://v8.angular.io/guide/ngmodule-api
@NgModule({
  // Static, that is compiler configuration
  declarations:[], // Configure the selectors
  entryComponents:[], // Generate the host factory

  // Runtime, or injector configuration
  providers: [], // Runtime injector configuration

  // Composability / Grouping
  imports: [], // composing NgModules together
  exports:[], // making NgModules available to other parts of the app
})
export class xxxModule { }
```

### template

```js
<ng-container *ngIf="filters?.length > 0; else noData">
  <div class="filter-item" *ngFor="let filter of filters">
    <app-tasks-filter-edit-item style="width: 100%" [data]="filter" [isChina]="isChinaInstance"
      (deleted)="onDeleteFilter($event)" (renamed)="onRenameFilter($event)" (edited)="onEditFilter($event)">
    </app-tasks-filter-edit-item>
  </div>
</ng-container>
<ng-template #noData>
  <div fxLayout="row" fxLayoutAlign="center center">
    <span>No filters found</span>
  </div>
</ng-template>
```

### [@angular/flex-layout](https://www.angularjswiki.com/flexlayout/fxlayout/)

### [ag-grid-angular](https://www.ag-grid.com/javascript-data-grid/)
