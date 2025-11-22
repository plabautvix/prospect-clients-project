import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CardLead } from './card-lead';

describe('CardLead', () => {
  let component: CardLead;
  let fixture: ComponentFixture<CardLead>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CardLead]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CardLead);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
