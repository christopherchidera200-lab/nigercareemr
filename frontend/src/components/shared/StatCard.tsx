interface StatCardProps {
  title:     string;
  value:     string | number;
  icon:      string;
  color:     'blue' | 'green' | 'amber' | 'red' | 'purple';
  subtitle?: string;
}

const colorMap = {
  blue:   'bg-blue-50 text-blue-700 border-blue-200',
  green:  'bg-green-50 text-green-700 border-green-200',
  amber:  'bg-amber-50 text-amber-700 border-amber-200',
  red:    'bg-red-50 text-red-700 border-red-200',
  purple: 'bg-purple-50 text-purple-700 border-purple-200',
};

const iconBgMap = {
  blue:   'bg-blue-100',
  green:  'bg-green-100',
  amber:  'bg-amber-100',
  red:    'bg-red-100',
  purple: 'bg-purple-100',
};

export default function StatCard({ title, value, icon, color, subtitle }: StatCardProps) {
  return (
    <div className={`card border ${colorMap[color].split(' ').slice(2).join(' ')}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${colorMap[color].split(' ').slice(1, 2).join(' ')}`}>
            {value}
          </p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${iconBgMap[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
