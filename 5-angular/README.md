# Angular

Interpolation {{ }}

```js
<a>
  {{ product.name }}
</a>
```

Property binding [ ]

```js
<a [title]="product.name + ' details'">
  {{ product.name }}
</a>
```

Event binding ( )

```js
<button (click)="share()">
  Share
</button>
```

## angular 8

@Input() 从父级传入 = react props

### html if else

```html
<div *ngIf="isPlannerScreen; else NonPlannerScreenMap" class="dropdown">
    <button class="dropbtn">
        <span class="material-icons">format_list_bulleted</span>
    </button>
    <div class="dropdown-content">
        <a [href]="garageURL" target="_blank" tsl-button color="white" class="custom-btn-white">Garage</a>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(2)">Honk Horn</button>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(4)">Hazards On</button>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(5)">Hazards Off</button>
    </div>
</div>
<ng-template #NonPlannerScreenMap>
    <div class="vin-actions">
        <a [href]="garageURL" target="_blank" tsl-button color="white" class="custom-btn-white">Garage</a>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(2)">Honk Horn</button>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(4)">Hazards On</button>
        <button type="button" [disabled]="isDisabledBtn" mat-raised-button class="custom-btn-white" (click)="performActionForVin(5)">Hazards Off</button>
    </div>
</ng-template>
```

### Route

```js
constructor(
  private actr: ActivatedRoute
) {
}

this.actr.snapshot.queryParams['rn']
```

### [pipe](https://angular.io/api/common/AsyncPipe)

```js
import { PipeTransform, Pipe } from '@angular/core';

@Pipe({ name: 'color' })
export class ColorPipe implements PipeTransform {

    transform(color: string): any {
        switch ((color || '').toLowerCase().replace('paint', '').trim()) {
          case 'black' : return 'black-flag';
          default: return 'custom-flag';
        }
    }
}

<span class='color' [ngClass]="dataItem.Color | color" matTooltip="Color: {{ dataItem.Color }}">
```

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

### [angular CDK Overlay](https://v8.material.angular.io/cdk/overlay/api)

Overlay 全局弹出层

```js
cosnt top = this.origin.elementRef.nativeElement.offsetTop;
cosnt left = this.origin.elementRef.nativeElement.offsetLeft;
return this.overlay.position().global().right().bottom().top(top).left(left);
```

相对于某元素的弹出层

```js
cosnt top = this.origin.elementRef.nativeElement.offsetTop;
cosnt left = this.origin.elementRef.nativeElement.offsetLeft;
return this.overlay.position().flexibleConnectedTo(this.origin.elementRef).withPositions([{
  originX: 'start',
  originY: 'top',
  overlayX: 'start',
  overlayY: 'top'
}]);
```

[源码分析](https://zhuanlan.zhihu.com/p/146996352)
1.计算 overlay 的可视性
2.选择最优的位置
3.应用位置

### [Angular Material Icon](https://material.io/resources/icons/?icon=sd_storage&style=baseline)

https://www.jianshu.com/p/a49e242aeac8

### [@angular/flex-layout](https://www.angularjswiki.com/flexlayout/fxlayout/)

### [ag-grid-angular](https://www.ag-grid.com/javascript-data-grid/)
