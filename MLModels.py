import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from matplotlib.patches import Patch

#Adjusted R² Function
def adjusted_r2(r2, n, p):
    return 1 - (1 - r2) * (n - 1) / (n - p - 1)

# Step 1: Data Preparation
df = pd.read_csv('data/gdpr_fines.csv')
gdp = pd.read_csv('data/country_gdp.csv')
pop = pd.read_csv('data/country_population.csv')

df['Fine_EUR'] = df['Fine'].astype(str).str.replace(',', '').astype(float)
df = df[df['Country'] != 'LIECHTENSTEIN'].copy()
print(f"Rows after dropping Liechtenstein: {len(df)}")

df['Log10_Fine'] = np.log10(df['Fine_EUR'])
df['Year'] = df['Date'].str[:4].astype(int)

def extract_article_count(text):
    if pd.isna(text) or text == 'Unknown':
        return 0
    return len(set(re.findall(r'Art\.?\s*(\d+)', str(text))))

df['Num_Articles'] = df['Articles Violated'].apply(extract_article_count)

df = df.merge(gdp[['Country', 'GDP_Millions_USD']], on='Country', how='left')
df = df.merge(pop[['Country', 'Population_Thousands']], on='Country', how='left')
df['GDP_Per_Capita_EUR'] = (df['GDP_Millions_USD'] * 0.924 * 1_000_000) / (df['Population_Thousands'] * 1000)

print(f"Missing GDP: {df['GDP_Millions_USD'].isna().sum()}")
print(f"Missing Population: {df['Population_Thousands'].isna().sum()}")

df_encoded = pd.get_dummies(df, columns=['Country', 'Sector', 'Type of Violation'], drop_first=True)

drop_cols = ['ETid', 'Authority', 'Date', 'Fine', 'Controller', 'Articles Violated',
             'Summary', 'Fine_EUR', 'Log10_Fine', 'GDP_Millions_USD']
feature_cols = [col for col in df_encoded.columns if col not in drop_cols]

X = df_encoded[feature_cols]
y = df_encoded['Log10_Fine']

country_features = [c for c in feature_cols if c.startswith('Country_')]
sector_features = [c for c in feature_cols if c.startswith('Sector_')]
type_features = [c for c in feature_cols if c.startswith('Type of Violation_')]

print(f"\nFeatures: {len(feature_cols)}")
print(f"Samples: {len(X)}")
print(f"\nFeature groups:")
print(f"  Country dummies: {len(country_features)}")
print(f"  Sector dummies: {len(sector_features)}")
print(f"  Type of Violation dummies: {len(type_features)}")
print(f"  Year: 1")
print(f"  Num_Articles: 1")
print(f"  GDP_Per_Capita_EUR: 1")
print(f"  Population_Thousands: 1")

# --- Step 2: Train/Test Split ---

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
n_test = len(X_test)
print(f"Training set: {len(X_train)} samples")
print(f"Test set: {n_test} samples")

# --- Step 3: Full Gradient Boosting with Tuning ---
param_grid = {
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 4, 5],
    'min_samples_leaf': [5, 10, 20],
    'subsample': [0.8, 1.0]}

gb = GradientBoostingRegressor(random_state=42)
grid_search = GridSearchCV(gb, param_grid, cv=5, scoring='neg_mean_squared_error',
                           n_jobs=-1, verbose=0)
grid_search.fit(X_train, y_train)

best_params = grid_search.best_params_
best_gb = grid_search.best_estimator_
y_pred_gb = best_gb.predict(X_test)

r2_full = r2_score(y_test, y_pred_gb)
adj_r2_full = adjusted_r2(r2_full, n_test, len(feature_cols))
rmse_full = np.sqrt(mean_squared_error(y_test, y_pred_gb))
mae_full = mean_absolute_error(y_test, y_pred_gb)

print(f"\nBest parameters: {best_params}")
print(f"Best CV RMSE: {np.sqrt(-grid_search.best_score_):.4f}")
print(f"\nTest set results:")
print(f"  R²:          {r2_full:.4f}")
print(f"  Adjusted R²: {adj_r2_full:.4f}")
print(f"  RMSE:        {rmse_full:.4f}")
print(f"  MAE:         {mae_full:.4f}")

# --- Step 4: Ablation - Violation + Year (Baseline) ---

violation_year_features = type_features + ['Num_Articles', 'Year']
print(f"Features: {len(violation_year_features)}")

gb_baseline = GradientBoostingRegressor(**best_params, random_state=42)
gb_baseline.fit(X_train[violation_year_features], y_train)
y_pred_baseline = gb_baseline.predict(X_test[violation_year_features])

r2_baseline = r2_score(y_test, y_pred_baseline)
adj_r2_baseline = adjusted_r2(r2_baseline, n_test, len(violation_year_features))
rmse_baseline = np.sqrt(mean_squared_error(y_test, y_pred_baseline))
mae_baseline = mean_absolute_error(y_test, y_pred_baseline)

print(f"  R²:          {r2_baseline:.4f}")
print(f"  Adjusted R²: {adj_r2_baseline:.4f}")
print(f"  RMSE:        {rmse_baseline:.4f}")
print(f"  MAE:         {mae_baseline:.4f}")

# --- Step 5: Ablation - Violation + Year + Location ---

location_add = country_features + ['GDP_Per_Capita_EUR', 'Population_Thousands']
violation_year_location_features = violation_year_features + location_add
print(f"Features: {len(violation_year_location_features)}")

gb_location = GradientBoostingRegressor(**best_params, random_state=42)
gb_location.fit(X_train[violation_year_location_features], y_train)
y_pred_location = gb_location.predict(X_test[violation_year_location_features])

r2_location = r2_score(y_test, y_pred_location)
adj_r2_location = adjusted_r2(r2_location, n_test, len(violation_year_location_features))
rmse_location = np.sqrt(mean_squared_error(y_test, y_pred_location))
mae_location = mean_absolute_error(y_test, y_pred_location)

print(f"  R²:          {r2_location:.4f}")
print(f"  Adjusted R²: {adj_r2_location:.4f}")
print(f"  RMSE:        {rmse_location:.4f}")
print(f"  MAE:         {mae_location:.4f}")
print(f"\n  Adjusted R² improvement from adding Location: +{adj_r2_location - adj_r2_baseline:.4f}")

# --- Step 6: Ablation - Violation + Year + Industry ---

violation_year_industry_features = violation_year_features + sector_features
print(f"Features: {len(violation_year_industry_features)}")

gb_industry = GradientBoostingRegressor(**best_params, random_state=42)
gb_industry.fit(X_train[violation_year_industry_features], y_train)
y_pred_industry = gb_industry.predict(X_test[violation_year_industry_features])

r2_industry = r2_score(y_test, y_pred_industry)
adj_r2_industry = adjusted_r2(r2_industry, n_test, len(violation_year_industry_features))
rmse_industry = np.sqrt(mean_squared_error(y_test, y_pred_industry))
mae_industry = mean_absolute_error(y_test, y_pred_industry)

print(f"  R²:          {r2_industry:.4f}")
print(f"  Adjusted R²: {adj_r2_industry:.4f}")
print(f"  RMSE:        {rmse_industry:.4f}")
print(f"  MAE:         {mae_industry:.4f}")
print(f"\n  Adjusted R² improvement from adding Industry: +{adj_r2_industry - adj_r2_baseline:.4f}")

# --- Step 7: Random Forest Robustness Check ---

rf = RandomForestRegressor(n_estimators=300, max_depth=10, min_samples_leaf=5,
                           random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

r2_rf = r2_score(y_test, y_pred_rf)
adj_r2_rf = adjusted_r2(r2_rf, n_test, len(feature_cols))
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
mae_rf = mean_absolute_error(y_test, y_pred_rf)

print(f"Random Forest Results:")
print(f"  R²:          {r2_rf:.4f}")
print(f"  Adjusted R²: {adj_r2_rf:.4f}")
print(f"  RMSE:        {rmse_rf:.4f}")
print(f"  MAE:         {mae_rf:.4f}")

# --- Step 8: Permutation Importance ---

perm_imp = permutation_importance(best_gb, X_test, y_test, n_repeats=10,
                                  random_state=42, n_jobs=-1)
imp_df = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': perm_imp.importances_mean,
    'Std': perm_imp.importances_std
}).sort_values('Importance', ascending=False)

print("Top 15 features by permutation importance:")
for _, row in imp_df.head(15).iterrows():
    print(f"  {row['Feature']:<50} {row['Importance']:.4f} (+/- {row['Std']:.4f})")

# Chart 1: Top 15 Individual Feature Importances
top15 = imp_df.head(15).sort_values('Importance', ascending=True)

def get_group_color(feat):
    if feat.startswith('Country_') or feat in ['GDP_Per_Capita_EUR', 'Population_Thousands']:
        return '#800020'
    elif feat.startswith('Sector_'):
        return '#4682b4'
    elif feat.startswith('Type of Violation_') or feat == 'Num_Articles':
        return '#2e8b57'
    else:
        return '#808080'

colors = [get_group_color(f) for f in top15['Feature']]

fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(range(len(top15)), top15['Importance'], xerr=top15['Std'],
        color=colors, capsize=3)
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(top15['Feature'], fontsize=9)
ax.set_xlabel('Permutation Importance')
ax.set_title('Top 15 Feature Importances (Gradient Boosting)')
legend_elements = [Patch(facecolor='#800020', label='Location'),
                   Patch(facecolor='#4682b4', label='Industry'),
                   Patch(facecolor='#2e8b57', label='Violation Nature'),
                   Patch(facecolor='#808080', label='Temporal')]
ax.legend(handles=legend_elements, loc='lower right')
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('analysis/feature_importance_top15.png', dpi=150, bbox_inches='tight', facecolor='white')

# Chart 2: Grouped Feature Importance
location_features = country_features + ['GDP_Per_Capita_EUR', 'Population_Thousands']
violation_features = type_features + ['Num_Articles']
temporal_features = ['Year']

location_imp = imp_df[imp_df['Feature'].isin(location_features)]['Importance'].sum()
industry_imp = imp_df[imp_df['Feature'].isin(sector_features)]['Importance'].sum()
violation_imp = imp_df[imp_df['Feature'].isin(violation_features)]['Importance'].sum()
temporal_imp = imp_df[imp_df['Feature'].isin(temporal_features)]['Importance'].sum()

total_imp = location_imp + industry_imp + violation_imp + temporal_imp
print(f"\nLocation (Country + GDP + Population): {location_imp:.4f} ({location_imp/total_imp*100:.1f}%)")
print(f"Industry (Sector):                     {industry_imp:.4f} ({industry_imp/total_imp*100:.1f}%)")
print(f"Violation Nature (Type + Num_Articles): {violation_imp:.4f} ({violation_imp/total_imp*100:.1f}%)")
print(f"Temporal (Year):                        {temporal_imp:.4f} ({temporal_imp/total_imp*100:.1f}%)")

groups = ['Location\n(Country, GDP,\nPopulation)', 'Industry\n(Sector)',
          'Violation Nature\n(Type, Num Articles)', 'Temporal\n(Year)']
group_vals = [location_imp, industry_imp, violation_imp, temporal_imp]
group_pcts = [v / total_imp * 100 for v in group_vals]
group_colors = ['#800020', '#4682b4', '#2e8b57', '#808080']

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(groups, group_vals, color=group_colors, width=0.6)
for bar, pct in zip(bars, group_pcts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
            f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)
ax.set_ylabel('Summed Permutation Importance')
ax.set_title('What Drives GDPR Fine Amounts?')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('analysis/grouped_importance.png', dpi=150, bbox_inches='tight', facecolor='white')

# Chart 3: GB vs RF Side-by-Side
perm_imp_rf = permutation_importance(rf, X_test, y_test, n_repeats=10,
                                     random_state=42, n_jobs=-1)
imp_df_rf = pd.DataFrame({'Feature': feature_cols, 'Importance': perm_imp_rf.importances_mean})

location_imp_rf = imp_df_rf[imp_df_rf['Feature'].isin(location_features)]['Importance'].sum()
industry_imp_rf = imp_df_rf[imp_df_rf['Feature'].isin(sector_features)]['Importance'].sum()
violation_imp_rf = imp_df_rf[imp_df_rf['Feature'].isin(violation_features)]['Importance'].sum()
temporal_imp_rf = imp_df_rf[imp_df_rf['Feature'].isin(temporal_features)]['Importance'].sum()

total_rf = location_imp_rf + industry_imp_rf + violation_imp_rf + temporal_imp_rf

group_labels = ['Location', 'Industry', 'Violation\nNature', 'Temporal']
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

axes[0].bar(group_labels, group_vals, color=group_colors, width=0.5)
for i, (val, pct) in enumerate(zip(group_vals, group_pcts)):
    axes[0].text(i, val + 0.002, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
axes[0].set_title('Gradient Boosting')
axes[0].set_ylabel('Summed Permutation Importance')
axes[0].grid(True, alpha=0.3, axis='y')

group_vals_rf = [location_imp_rf, industry_imp_rf, violation_imp_rf, temporal_imp_rf]
group_pcts_rf = [v / total_rf * 100 for v in group_vals_rf]
axes[1].bar(group_labels, group_vals_rf, color=group_colors, width=0.5)
for i, (val, pct) in enumerate(zip(group_vals_rf, group_pcts_rf)):
    axes[1].text(i, val + 0.002, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
axes[1].set_title('Random Forest')
axes[1].grid(True, alpha=0.3, axis='y')

plt.suptitle('Grouped Feature Importance: Model Comparison', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('analysis/model_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')

# Chart 4: Actual vs Predicted
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(y_test, y_pred_gb, alpha=0.3, s=15, color='#4682b4')
min_val = min(y_test.min(), y_pred_gb.min())
max_val = max(y_test.max(), y_pred_gb.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect prediction')
ax.set_xlabel('Actual Log10(Fine)')
ax.set_ylabel('Predicted Log10(Fine)')
ax.set_title(f'Actual vs Predicted (Adjusted R² = {adj_r2_full:.3f})')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('analysis/actual_vs_predicted.png', dpi=150, bbox_inches='tight', facecolor='white')

